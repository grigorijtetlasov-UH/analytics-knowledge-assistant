import psycopg
import pytest

from app.answer import (
    OFF_TOPIC_MESSAGE,
    SYSTEM_PROMPT,
    AnswerValidationError,
    Source,
    answer_question,
    build_user_message,
    off_topic_answer,
    validate,
)
from app.docs import load_documents
from app.ingest import ingest
from app.llm import AnswerStatus, ModelAnswer
from app.migrate import migrate
from app.retrieval import SearchResult
from tests.fakes import FakeEmbedder, FakeLLM


def chunk(doc_id: str, section: str = "Formula") -> SearchResult:
    return SearchResult(0, doc_id, doc_id.upper(), section, f"{doc_id} text", 0.5)


CHUNKS = [chunk("aov"), chunk("gmv", "Definition"), chunk("aov", "Pitfalls")]


def model_answer(
    status: AnswerStatus = AnswerStatus.ANSWERED,
    source_ids: list[int] | None = None,
    text: str = "answer",
    clarifying_question: str | None = None,
) -> ModelAnswer:
    return ModelAnswer(
        status=status,
        answer=text,
        clarifying_question=clarifying_question,
        source_ids=[1] if source_ids is None else source_ids,
    )


# --- prompt ---


def test_user_message_numbers_sources_and_shows_availability() -> None:
    message = build_user_message("What is AOV?", CHUNKS[:2], {"aov": "full", "gmv": "partial"})
    assert (
        '<source id="S1" doc_id="aov" section="Formula" data_availability="full">\naov text'
        in message
    )
    assert '<source id="S2" doc_id="gmv" section="Definition" data_availability="partial">' in (
        message
    )
    assert message.endswith("<question>\nWhat is AOV?\n</question>")


def test_system_prompt_is_static() -> None:
    # Prompt caching needs a byte-identical prefix; nothing per-request may leak into it.
    assert "{" not in SYSTEM_PROMPT


# --- validation ---


def test_validate_returns_cited_sources_deduplicated_in_order() -> None:
    sources = validate(model_answer(source_ids=[2, 1, 2]), CHUNKS)
    assert sources == [Source("gmv", "GMV", "Definition"), Source("aov", "AOV", "Formula")]


def test_inline_markers_count_as_citations() -> None:
    sources = validate(model_answer(source_ids=[], text="see [S3]"), CHUNKS)
    assert sources == [Source("aov", "AOV", "Pitfalls")]


@pytest.mark.parametrize(
    "answer",
    [
        model_answer(source_ids=[4]),  # only S1..S3 were given
        model_answer(source_ids=[0]),
        model_answer(source_ids=[1], text="as [S7] says"),
    ],
)
def test_invented_source_is_rejected(answer: ModelAnswer) -> None:
    with pytest.raises(AnswerValidationError, match="only S1..S3"):
        validate(answer, CHUNKS)


@pytest.mark.parametrize(
    "status", [AnswerStatus.ANSWERED, AnswerStatus.NO_DATA, AnswerStatus.AMBIGUOUS]
)
def test_answer_without_sources_is_rejected(status: AnswerStatus) -> None:
    answer = model_answer(status, source_ids=[], clarifying_question="Which one?")
    with pytest.raises(AnswerValidationError, match="without any source"):
        validate(answer, CHUNKS)


def test_off_topic_may_have_no_sources() -> None:
    assert validate(model_answer(AnswerStatus.OFF_TOPIC, source_ids=[]), CHUNKS) == []


def test_ambiguous_needs_a_clarifying_question() -> None:
    with pytest.raises(AnswerValidationError, match="clarifying question"):
        validate(model_answer(AnswerStatus.AMBIGUOUS, source_ids=[1, 2]), CHUNKS)


def test_off_topic_message_follows_question_language() -> None:
    assert off_topic_answer("Яка погода?").answer == OFF_TOPIC_MESSAGE["uk"]
    assert off_topic_answer("What's the weather?").answer == OFF_TOPIC_MESSAGE["en"]


# --- pipeline with a real database, fake embeddings and a fake LLM ---


@pytest.fixture
def indexed_conn(db_conn: psycopg.Connection) -> psycopg.Connection:
    migrate(db_conn)
    ingest(db_conn, load_documents(), FakeEmbedder())
    return db_conn


def aov_formula_text(conn: psycopg.Connection) -> str:
    """A 'question' whose fake embedding equals the AOV Formula chunk's: similarity 1.0."""
    return conn.execute(
        "SELECT content FROM rag.chunks WHERE doc_id = 'aov' AND section = 'Formula'"
    ).fetchone()[0]


@pytest.mark.db
def test_question_below_threshold_does_not_call_llm(indexed_conn: psycopg.Connection) -> None:
    llm = FakeLLM(model_answer())
    # Random fake vectors have similarity ~0 with every chunk.
    result = answer_question(indexed_conn, "unrelated", FakeEmbedder(), llm, min_similarity=0.22)
    assert result.status == AnswerStatus.OFF_TOPIC
    assert result.model is None and result.cost_usd is None
    assert llm.calls == []


@pytest.mark.db
def test_answer_cites_retrieved_chunks(indexed_conn: psycopg.Connection) -> None:
    llm = FakeLLM(model_answer(source_ids=[1], text="AOV = GMV / orders [S1]"))
    question = aov_formula_text(indexed_conn)

    result = answer_question(indexed_conn, question, FakeEmbedder(), llm, min_similarity=0.22)

    assert result.status == AnswerStatus.ANSWERED
    assert result.sources == [Source("aov", "Average Order Value", "Formula")]
    assert result.model == "claude-opus-5-5"
    # FakeLLM reports 1000 input + 200 output tokens: 1000 * $4/1M + 200 * $20/1M.
    assert result.cost_usd == pytest.approx(0.008)
    [(system, user)] = llm.calls
    assert system == SYSTEM_PROMPT
    assert '<source id="S1" doc_id="aov" section="Formula" data_availability="full">' in user
    assert user.count("<source ") == 5


@pytest.mark.db
def test_clarifying_question_is_dropped_unless_ambiguous(
    indexed_conn: psycopg.Connection,
) -> None:
    llm = FakeLLM(model_answer(clarifying_question="Which one?"))
    question = aov_formula_text(indexed_conn)
    result = answer_question(indexed_conn, question, FakeEmbedder(), llm, min_similarity=0.22)
    assert result.clarifying_question is None
