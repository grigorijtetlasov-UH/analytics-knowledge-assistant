from pathlib import Path

import pytest

from evals.run_evals import CachedEmbedder, first_hit_rank, load_cases, summarize
from tests.fakes import FakeEmbedder


def test_testset_is_valid_and_covers_every_document() -> None:
    cases = load_cases()
    doc_ids = {p.stem for p in Path("data/docs").glob("*.md")}
    expected = {doc for c in cases for doc in c.expected}
    assert expected == doc_ids
    # Every intent is asked in both languages: the en/uk comparison relies on pairs.
    by_id: dict[str, set[str]] = {}
    for case in cases:
        by_id.setdefault(case.id, set()).add(case.lang)
    assert all(langs == {"en", "uk"} for langs in by_id.values())
    assert all(case.question.strip() for case in cases)


def test_first_hit_rank() -> None:
    expected = frozenset({"gmv", "conventions"})
    assert first_hit_rank(["aov", "gmv", "gmv"], expected) == 2
    assert first_hit_rank(["aov", "clv"], expected) is None
    assert first_hit_rank([], expected) is None


def test_summarize() -> None:
    summary = summarize([1, 3, None, 6])
    assert summary["hit@1"] == 0.25
    assert summary["hit@3"] == 0.5
    assert summary["hit@5"] == 0.5
    # rank 6 is beyond K=5, so it adds nothing to MRR@5
    assert summary["MRR@5"] == pytest.approx((1 + 1 / 3) / 4)


def test_cached_embedder_calls_the_api_once_per_text(tmp_path: Path) -> None:
    inner = FakeEmbedder()
    cache = tmp_path / "cache.json"

    first = CachedEmbedder(inner, 1536, cache).embed(["a", "b", "a"])
    second = CachedEmbedder(inner, 1536, cache).embed(["b", "a"])  # new instance, same file

    assert inner.embedded == ["a", "b"]
    assert first == [FakeEmbedder.vector("a"), FakeEmbedder.vector("b"), FakeEmbedder.vector("a")]
    assert second == [FakeEmbedder.vector("b"), FakeEmbedder.vector("a")]
