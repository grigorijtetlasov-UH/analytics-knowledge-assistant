from types import SimpleNamespace
from typing import Any

import anthropic
import httpx2 as httpx
import pytest

from app.llm import (
    FALLBACK_BETA,
    MAX_TOKENS,
    AnswerStatus,
    AnthropicLLM,
    LLMError,
    ModelAnswer,
    Usage,
    cost_usd,
)

# The Anthropic client is replaced by a stub: these tests check how we build the request
# and read the response, without network, key or cost.

ANSWER = ModelAnswer(
    status=AnswerStatus.ANSWERED,
    answer="AOV = GMV / orders [S1]",
    clarifying_question=None,
    source_ids=[1],
)


class StubMessages:
    def __init__(self, response: Any = None, error: Exception | None = None) -> None:
        self.response = response
        self.error = error
        self.kwargs: dict[str, Any] = {}

    def parse(self, **kwargs: Any) -> Any:
        self.kwargs = kwargs
        if self.error is not None:
            raise self.error
        return self.response


def stub_client(messages: StubMessages) -> Any:
    return SimpleNamespace(beta=SimpleNamespace(messages=messages))


def response(stop_reason: str = "end_turn", parsed: ModelAnswer | None = ANSWER) -> Any:
    usage = SimpleNamespace(
        input_tokens=1500,
        output_tokens=300,
        cache_read_input_tokens=700,
        cache_creation_input_tokens=None,
    )
    return SimpleNamespace(
        stop_reason=stop_reason, parsed_output=parsed, model="claude-opus-5-5", usage=usage
    )


def test_request_shape_for_opus_includes_fallback_and_cache() -> None:
    messages = StubMessages(response())
    result = AnthropicLLM(stub_client(messages), "claude-opus-5-5", "low").answer("SYS", "Q")

    kwargs = messages.kwargs
    assert kwargs["model"] == "claude-opus-5-5"
    assert kwargs["max_tokens"] == MAX_TOKENS
    assert kwargs["system"] == [
        {"type": "text", "text": "SYS", "cache_control": {"type": "ephemeral"}}
    ]
    assert kwargs["messages"] == [{"role": "user", "content": "Q"}]
    assert kwargs["output_config"] == {"effort": "low"}
    assert kwargs["output_format"] is ModelAnswer
    assert kwargs["betas"] == [FALLBACK_BETA]
    assert kwargs["fallbacks"] == "default"

    assert result.answer == ANSWER
    assert result.model == "claude-opus-5-5"
    assert result.usage == Usage(1500, 300, cache_read_input_tokens=700)


def test_haiku_gets_no_fallback() -> None:
    # Haiku 5.5 has no server-side fallback: sending the parameter would be rejected.
    messages = StubMessages(response())
    AnthropicLLM(stub_client(messages), "claude-haiku-5-5", "low").answer("SYS", "Q")
    assert "fallbacks" not in messages.kwargs
    assert "betas" not in messages.kwargs


@pytest.mark.parametrize(
    ("resp", "message"),
    [
        (response(stop_reason="refusal", parsed=None), "declined"),
        (response(stop_reason="max_tokens", parsed=None), "truncated"),
        (response(parsed=None), "no structured answer"),
    ],
)
def test_unusable_responses_raise(resp: Any, message: str) -> None:
    llm = AnthropicLLM(stub_client(StubMessages(resp)), "claude-opus-5-5", "low")
    with pytest.raises(LLMError, match=message) as info:
        llm.answer("SYS", "Q")
    assert info.value.retryable is False


def api_error(cls: type[anthropic.APIStatusError], status: int) -> anthropic.APIStatusError:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return cls("error", response=httpx.Response(status, request=request), body=None)


@pytest.mark.parametrize(
    ("error", "retryable"),
    [
        (api_error(anthropic.RateLimitError, 429), True),
        (api_error(anthropic.InternalServerError, 500), True),
        (api_error(anthropic.BadRequestError, 400), False),
        (api_error(anthropic.AuthenticationError, 401), False),
    ],
)
def test_api_errors_are_wrapped(error: Exception, retryable: bool) -> None:
    llm = AnthropicLLM(stub_client(StubMessages(error=error)), "claude-opus-5-5", "low")
    with pytest.raises(LLMError) as info:
        llm.answer("SYS", "Q")
    assert info.value.retryable is retryable


def test_cost_usd() -> None:
    usage = Usage(
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_read_input_tokens=1_000_000,
        cache_creation_input_tokens=1_000_000,
    )
    # Opus 5.5: $4 input + $20 output + $0.20 cache read + $5 cache write per 1M tokens.
    assert cost_usd("claude-opus-5-5", usage) == pytest.approx(29.20)
    assert cost_usd("claude-haiku-5-5", Usage(2000, 500)) == pytest.approx(0.00045)


def test_cost_of_unknown_model_is_none() -> None:
    assert cost_usd("claude-opus-4-8", Usage(1000, 100)) is None
