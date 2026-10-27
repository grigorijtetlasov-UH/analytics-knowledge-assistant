"""Claude client for /ask: one structured-output call per question, plus its cost.

The answer pipeline (app/answer.py) depends on the small `LLM` protocol, not on Anthropic
directly, so unit tests use a fake and never call the API (same idea as app/embeddings.py).

Why structured output (`output_format=ModelAnswer`): the pipeline branches on `status`
(answered / ambiguous / no_data / off_topic) and validates the cited source numbers. With a
JSON schema enforced by the API, those fields are always present and typed; parsing free
text would fail in ways we only find in production. Anthropic's built-in Citations cannot
be combined with structured output, so sources are cited by number ([S1]..[S5]) instead.
"""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

import anthropic
from pydantic import BaseModel, Field

# Enough for a short answer plus the reasoning at effort "low"; a hit is reported as an
# error instead of returning a truncated answer.
MAX_TOKENS = 4000

# Server-side fallback: if the model's safety classifiers decline a request, the API re-runs
# it on a model Anthropic picks for that refusal category, inside the same call. "default"
# avoids pinning a fallback model that would later be deprecated. Haiku 5.5 has no
# server-side fallback (the parameter would be rejected or do nothing), so it is not sent.
FALLBACK_BETA = "server-side-fallback-2026-07-01"
MODELS_WITH_SERVER_FALLBACK = frozenset({"claude-opus-5-5", "claude-sonnet-5-5"})


class AnswerStatus(StrEnum):
    ANSWERED = "answered"  # the documents answer the question
    AMBIGUOUS = "ambiguous"  # the term fits several metrics: both explained + a question back
    NO_DATA = "no_data"  # defined in the docs, but not computable from the Olist data
    OFF_TOPIC = "off_topic"  # the documents do not cover the question


class ModelAnswer(BaseModel):
    """The JSON schema the model must fill. Field descriptions are part of the prompt:
    the API sends them to the model with the schema."""

    status: AnswerStatus
    answer: str = Field(description="The answer, in the language of the question.")
    clarifying_question: str | None = Field(
        description="Only for status=ambiguous: one question that resolves the ambiguity."
    )
    source_ids: list[int] = Field(
        description="Numbers of the sources the answer relies on: 1 for [S1], 2 for [S2]..."
    )


@dataclass(frozen=True)
class Price:
    """USD per million tokens."""

    input: float
    output: float
    cache_write: float  # 5-minute cache write
    cache_read: float


# From claude.com/pricing (checked 2026-10-27). Haiku 5.5 prices are for prompts up to 100K
# tokens; ours are ~2K. A model missing here (e.g. a fallback model) gets cost None
# rather than a wrong number.
PRICES: dict[str, Price] = {
    "claude-opus-5-5": Price(input=4.00, output=20.00, cache_write=5.00, cache_read=0.20),
    "claude-sonnet-5-5": Price(input=2.00, output=10.00, cache_write=2.50, cache_read=0.10),
    "claude-haiku-5-5": Price(input=0.10, output=0.50, cache_write=0.125, cache_read=0.01),
}


@dataclass(frozen=True)
class Usage:
    input_tokens: int  # uncached input
    output_tokens: int  # includes thinking tokens
    cache_read_input_tokens: int = 0
    cache_creation_input_tokens: int = 0


def cost_usd(model: str, usage: Usage) -> float | None:
    price = PRICES.get(model)
    if price is None:
        return None
    total = (
        usage.input_tokens * price.input
        + usage.output_tokens * price.output
        + usage.cache_creation_input_tokens * price.cache_write
        + usage.cache_read_input_tokens * price.cache_read
    )
    return round(total / 1_000_000, 6)


@dataclass(frozen=True)
class LLMResult:
    answer: ModelAnswer
    model: str  # the model that produced the answer (differs from the requested on fallback)
    usage: Usage


class LLMError(Exception):
    """The model gave no usable answer (refusal, truncation, API failure)."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        # True when trying again later may work (rate limit, overload, network).
        self.retryable = retryable


class LLM(Protocol):
    model: str

    def answer(self, system: str, user: str) -> LLMResult: ...


class AnthropicLLM:
    def __init__(self, client: anthropic.Anthropic, model: str, effort: str) -> None:
        self.model = model
        self.effort = effort
        self._client = client

    def answer(self, system: str, user: str) -> LLMResult:
        fallback: dict[str, object] = (
            {"betas": [FALLBACK_BETA], "fallbacks": "default"}
            if self.model in MODELS_WITH_SERVER_FALLBACK
            else {}
        )
        try:
            # The beta namespace is needed only for `fallbacks`; parse() validates the JSON
            # against ModelAnswer. The SDK already retries 429/5xx/network errors twice.
            response = self._client.beta.messages.parse(
                model=self.model,
                max_tokens=MAX_TOKENS,
                # The system prompt never changes between requests (no dates, no ids), so it
                # is cached: repeated questions within 5 minutes read it at ~5% of the price.
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                messages=[{"role": "user", "content": user}],
                output_config={"effort": self.effort},
                output_format=ModelAnswer,
                **fallback,
            )
        except (anthropic.RateLimitError, anthropic.InternalServerError) as exc:
            raise LLMError(f"Claude API unavailable: {exc}", retryable=True) from exc
        except anthropic.APIConnectionError as exc:
            raise LLMError(f"cannot reach Claude API: {exc}", retryable=True) from exc
        except anthropic.APIStatusError as exc:
            # 400/401/403/404: a bug or a configuration problem; retrying will not help.
            raise LLMError(f"Claude API error {exc.status_code}: {exc.message}") from exc

        # Check stop_reason before reading the content: on a refusal it may be empty.
        if response.stop_reason == "refusal":
            raise LLMError("the model declined to answer")
        if response.stop_reason == "max_tokens":
            raise LLMError(f"answer truncated at max_tokens={MAX_TOKENS}")
        if response.parsed_output is None:
            raise LLMError("no structured answer in the response")

        # After a fallback, top-level usage covers only the attempt that produced the answer
        # (a declined attempt is listed separately in usage.iterations). Refusals on metric
        # questions are unlikely, so the cost of a declined attempt is not added here.
        u = response.usage
        usage = Usage(
            input_tokens=u.input_tokens,
            output_tokens=u.output_tokens,
            cache_read_input_tokens=u.cache_read_input_tokens or 0,
            cache_creation_input_tokens=u.cache_creation_input_tokens or 0,
        )
        return LLMResult(answer=response.parsed_output, model=response.model, usage=usage)
