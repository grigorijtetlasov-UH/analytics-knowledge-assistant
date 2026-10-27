"""REST API: POST /ask answers a question from the metric documents, GET /health checks the DB.

Run: uv run python -m uvicorn app.api:app --reload

Endpoints are plain `def`, not `async def`: psycopg, OpenAI and Anthropic clients used here
are synchronous, and FastAPI runs sync endpoints in a thread pool, so a slow LLM call does
not block other requests.

Dependencies (connection, embedder, LLM, settings) are injected with Depends(), so tests
replace them with a test database and fakes via app.dependency_overrides.

Error mapping: the client always gets either a valid answer or an HTTP error, never an
answer without sources.
- 422: invalid request (empty or too long question), from Pydantic;
- 502: an upstream service returned something unusable (model refusal, truncated or
  invalid answer, a non-retryable API error);
- 503: a dependency is unavailable or not configured (DB down, rate limit, missing key);
  trying again later may work.
"""

import logging
from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

import anthropic
import openai
import psycopg
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.answer import Answer, AnswerValidationError, answer_question
from app.config import Settings, get_settings
from app.db import connect
from app.embeddings import Embedder, OpenAIEmbedder
from app.llm import LLM, AnswerStatus, AnthropicLLM, LLMError

logger = logging.getLogger(__name__)

# Long enough for any real question; stops someone pasting a whole document into the prompt.
MAX_QUESTION_CHARS = 1000

app = FastAPI(
    title="Analytics Knowledge Assistant",
    description="Answers questions about e-commerce metrics with cited sources.",
    version="0.1.0",
)


# --- request / response models (the public API contract) ---


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)


class SourceOut(BaseModel):
    doc_id: str  # e.g. "aov"; the file data/docs/<doc_id>.md
    name: str  # e.g. "Average Order Value"
    section: str  # e.g. "Formula"


class UsageOut(BaseModel):
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: int
    cache_creation_input_tokens: int
    cost_usd: float | None  # None for a model without a known price


class AskResponse(BaseModel):
    status: AnswerStatus
    answer: str
    clarifying_question: str | None
    sources: list[SourceOut]
    model: str | None  # None when the question was rejected without calling the LLM
    usage: UsageOut | None


class HealthResponse(BaseModel):
    status: str
    chunks: int  # indexed chunks for the configured embedding model; 0 means "run ingest"


def to_response(answer: Answer) -> AskResponse:
    usage = (
        None
        if answer.usage is None
        else UsageOut(
            input_tokens=answer.usage.input_tokens,
            output_tokens=answer.usage.output_tokens,
            cache_read_input_tokens=answer.usage.cache_read_input_tokens,
            cache_creation_input_tokens=answer.usage.cache_creation_input_tokens,
            cost_usd=answer.cost_usd,
        )
    )
    return AskResponse(
        status=answer.status,
        answer=answer.answer,
        clarifying_question=answer.clarifying_question,
        sources=[
            SourceOut(doc_id=s.doc_id, name=s.name, section=s.section) for s in answer.sources
        ],
        model=answer.model,
        usage=usage,
    )


# --- dependencies ---

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_conn(settings: SettingsDep) -> Iterator[psycopg.Connection]:
    """One connection per request, closed afterwards. Enough for a demo; a pool
    (psycopg_pool) is the next step if the API ever gets real traffic."""
    try:
        conn = connect(settings, autocommit=True)
    except psycopg.OperationalError as exc:
        logger.error("database unavailable: %s", exc)
        raise HTTPException(503, "database unavailable") from exc
    with conn:
        yield conn


# Clients are cached per key: creating one per request would open a new HTTP connection
# pool each time.
@lru_cache
def openai_client(api_key: str) -> openai.OpenAI:
    return openai.OpenAI(api_key=api_key)


@lru_cache
def anthropic_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


def get_embedder(settings: SettingsDep) -> Embedder:
    if settings.openai_api_key is None:
        raise HTTPException(503, "OPENAI_API_KEY is not configured")
    client = openai_client(settings.openai_api_key.get_secret_value())
    return OpenAIEmbedder(client, settings.embedding_model, settings.embedding_dimensions)


def get_llm(settings: SettingsDep) -> LLM:
    if settings.anthropic_api_key is None:
        raise HTTPException(503, "ANTHROPIC_API_KEY is not configured")
    client = anthropic_client(settings.anthropic_api_key.get_secret_value())
    return AnthropicLLM(client, settings.llm_model, settings.llm_effort)


# --- endpoints ---


@app.post("/ask", response_model=AskResponse)
def ask(
    request: AskRequest,
    settings: SettingsDep,
    conn: Annotated[psycopg.Connection, Depends(get_conn)],
    embedder: Annotated[Embedder, Depends(get_embedder)],
    llm: Annotated[LLM, Depends(get_llm)],
) -> AskResponse:
    try:
        answer = answer_question(
            conn,
            request.question,
            embedder,
            llm,
            min_similarity=settings.off_topic_min_similarity,
        )
    except (openai.APIConnectionError, openai.RateLimitError, openai.InternalServerError) as exc:
        logger.error("embeddings API unavailable: %s", exc)
        raise HTTPException(503, "embeddings service unavailable") from exc
    except openai.APIError as exc:
        logger.error("embeddings API error: %s", exc)
        raise HTTPException(502, "embeddings service error") from exc
    except LLMError as exc:
        logger.error("LLM error: %s", exc)
        raise HTTPException(503 if exc.retryable else 502, str(exc)) from exc
    except AnswerValidationError as exc:
        # The model broke a rule (e.g. cited a source it was not given). Logged with the
        # question so the case can become an eval; the user gets an error, not the answer.
        logger.warning("invalid model answer: %s; question=%r", exc, request.question)
        raise HTTPException(502, "the model returned an invalid answer") from exc
    return to_response(answer)


@app.get("/health", response_model=HealthResponse)
def health(
    settings: SettingsDep, conn: Annotated[psycopg.Connection, Depends(get_conn)]
) -> HealthResponse:
    """Checks only the database (and that the index is filled), not the paid APIs: a health
    probe that runs every few seconds must not cost money."""
    try:
        [chunks] = conn.execute(
            "SELECT count(*) FROM rag.chunks WHERE embedding_model = %s",
            (settings.embedding_model,),
        ).fetchone()
    except psycopg.errors.UndefinedTable as exc:
        raise HTTPException(503, "database is not migrated: run app.migrate") from exc
    return HealthResponse(status="ok", chunks=chunks)
