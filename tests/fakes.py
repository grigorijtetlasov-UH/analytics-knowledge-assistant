"""Test doubles shared by several test modules."""

import hashlib
import random

from app.llm import LLMResult, ModelAnswer, Usage

DIMENSIONS = 1536  # must match rag.chunks.embedding


class FakeEmbedder:
    """Deterministic embeddings derived from a hash of the text; records what it embedded.
    Vectors are random, so they carry no meaning: tests with it check plumbing, not quality."""

    def __init__(self, model: str = "fake-model") -> None:
        self.model = model
        self.embedded: list[str] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.embedded += texts
        return [self.vector(text) for text in texts]

    @staticmethod
    def vector(text: str) -> list[float]:
        seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")
        rng = random.Random(seed)
        return [rng.uniform(-1, 1) for _ in range(DIMENSIONS)]


class FakeLLM:
    """Returns a fixed answer and records the prompts it was given."""

    def __init__(self, answer: ModelAnswer, model: str = "claude-opus-5-5") -> None:
        self.model = model
        self._answer = answer
        self.calls: list[tuple[str, str]] = []  # (system, user)

    def answer(self, system: str, user: str) -> LLMResult:
        self.calls.append((system, user))
        usage = Usage(input_tokens=1000, output_tokens=200)
        return LLMResult(answer=self._answer, model=self.model, usage=usage)
