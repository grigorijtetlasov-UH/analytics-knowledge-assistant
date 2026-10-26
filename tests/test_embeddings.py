from types import SimpleNamespace
from typing import Any

from app.embeddings import BATCH_SIZE, OpenAIEmbedder


class FakeOpenAIClient:
    """Mimics client.embeddings.create(); returns items in reverse order, like an API that
    does not guarantee ordering, with the input index encoded in the vector."""

    def __init__(self) -> None:
        self.embeddings = self
        self.calls: list[dict[str, Any]] = []

    def create(self, *, model: str, input: list[str], dimensions: int) -> SimpleNamespace:
        self.calls.append({"model": model, "size": len(input), "dimensions": dimensions})
        data = [
            SimpleNamespace(index=i, embedding=[float(len(text))] * dimensions)
            for i, text in enumerate(input)
        ]
        return SimpleNamespace(data=data[::-1], usage=SimpleNamespace(total_tokens=len(input)))


def test_openai_embedder_batches_and_keeps_input_order() -> None:
    client = FakeOpenAIClient()
    embedder = OpenAIEmbedder(client, "test-model", dimensions=3)  # type: ignore[arg-type]
    texts = ["x" * n for n in range(1, BATCH_SIZE + 6)]  # one full batch + 5

    vectors = embedder.embed(texts)

    assert [c["size"] for c in client.calls] == [BATCH_SIZE, 5]
    assert all(c["model"] == "test-model" and c["dimensions"] == 3 for c in client.calls)
    assert [v[0] for v in vectors] == [float(len(t)) for t in texts]
    assert embedder.total_tokens == len(texts)


def test_openai_embedder_with_no_texts_makes_no_calls() -> None:
    client = FakeOpenAIClient()
    embedder = OpenAIEmbedder(client, "test-model", dimensions=3)  # type: ignore[arg-type]
    assert embedder.embed([]) == []
    assert client.calls == []
