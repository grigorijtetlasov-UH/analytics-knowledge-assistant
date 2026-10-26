"""Text embeddings.

Ingestion depends on the small `Embedder` protocol rather than on OpenAI directly, so tests
use a deterministic fake and never call the API (no key needed in CI, no cost, no flakiness).
"""

from typing import Protocol

from openai import OpenAI

# The API accepts up to 2048 inputs per request; 100 keeps each request small.
BATCH_SIZE = 100


class Embedder(Protocol):
    # Stored with every chunk: vectors from different models must never be mixed.
    model: str

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per text, in the same order."""
        ...


class OpenAIEmbedder:
    def __init__(self, client: OpenAI, model: str, dimensions: int) -> None:
        self.model = model
        self.dimensions = dimensions
        self.total_tokens = 0  # reported by the ingest CLI
        self._client = client

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), BATCH_SIZE):
            response = self._client.embeddings.create(
                model=self.model,
                input=texts[start : start + BATCH_SIZE],
                dimensions=self.dimensions,
            )
            # Each item carries the index of its input; sort instead of trusting the order.
            data = sorted(response.data, key=lambda item: item.index)
            vectors += [item.embedding for item in data]
            self.total_tokens += response.usage.total_tokens
        return vectors
