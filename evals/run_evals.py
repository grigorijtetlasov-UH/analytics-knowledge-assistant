"""Measure retrieval quality on evals/testset.json.

Usage: uv run python -m evals.run_evals --label baseline [--modes vector]

For every question (each intent in English and Ukrainian) the search returns the top K
chunks. A question is a hit at k if any chunk among the first k comes from one of its
expected documents. Reported per mode, language and question kind:
- hit@1, hit@3, hit@5: share of questions with a hit at that depth;
- MRR@5: mean of 1 / rank of the first hit (0 when there is none in the top 5).

The full report (with the misses) is written to evals/results/retrieval_<label>.md;
the console gets the summary table only.
"""

import argparse
import hashlib
import json
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import psycopg
from openai import OpenAI

from app.config import get_settings
from app.db import connect
from app.embeddings import Embedder, OpenAIEmbedder
from app.retrieval import SearchResult, search_vector

TESTSET_PATH = Path("evals/testset.json")
RESULTS_DIR = Path("evals/results")
# Query embeddings are cached so re-runs are free and use identical vectors.
CACHE_PATH = Path("evals/.cache/query_embeddings.json")
K = 5
HIT_DEPTHS = (1, 3, 5)


@dataclass(frozen=True)
class Case:
    id: str  # "q01"
    lang: str  # "en" | "uk"
    kind: str  # name | alias | paraphrase | availability
    question: str
    expected: frozenset[str]


@dataclass(frozen=True)
class Query:
    """What a search mode receives: the question text and its embedding."""

    text: str
    embedding: list[float]
    model: str


SearchFn = Callable[[psycopg.Connection, Query], list[SearchResult]]

MODES: dict[str, SearchFn] = {
    "vector": lambda conn, q: search_vector(conn, q.embedding, q.model, K),
}


def load_cases(path: Path = TESTSET_PATH) -> list[Case]:
    items = json.loads(path.read_text(encoding="utf-8"))["items"]
    return [
        Case(item["id"], lang, item["kind"], question, frozenset(item["expected_doc_ids"]))
        for item in items
        for lang, question in item["questions"].items()
    ]


def first_hit_rank(doc_ids: list[str], expected: frozenset[str]) -> int | None:
    """1-based position of the first result from an expected document, None if absent."""
    for rank, doc_id in enumerate(doc_ids, start=1):
        if doc_id in expected:
            return rank
    return None


def summarize(ranks: list[int | None]) -> dict[str, float]:
    n = len(ranks)
    summary = {
        f"hit@{depth}": sum(1 for r in ranks if r is not None and r <= depth) / n
        for depth in HIT_DEPTHS
    }
    summary[f"MRR@{K}"] = sum(1 / r for r in ranks if r is not None and r <= K) / n
    return summary


class CachedEmbedder:
    """Wraps an embedder with a JSON file cache keyed by model, size and text."""

    def __init__(self, inner: Embedder, dimensions: int, path: Path = CACHE_PATH) -> None:
        self.model = inner.model
        self._inner = inner
        self._dimensions = dimensions
        self._path = path
        self._cache: dict[str, list[float]] = (
            json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        )

    def _key(self, text: str) -> str:
        raw = f"{self.model}|{self._dimensions}|{text}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def embed(self, texts: list[str]) -> list[list[float]]:
        missing = list(dict.fromkeys(t for t in texts if self._key(t) not in self._cache))
        if missing:
            for text, vector in zip(missing, self._inner.embed(missing), strict=True):
                self._cache[self._key(text)] = vector
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(self._cache), encoding="utf-8")
        return [self._cache[self._key(t)] for t in texts]


@dataclass(frozen=True)
class Outcome:
    case: Case
    mode: str
    doc_ids: list[str]  # documents of the top-K chunks, in rank order
    rank: int | None


def run(
    conn: psycopg.Connection, cases: list[Case], embedder: Embedder, modes: list[str]
) -> list[Outcome]:
    embeddings = embedder.embed([c.question for c in cases])
    outcomes = []
    for mode in modes:
        for case, embedding in zip(cases, embeddings, strict=True):
            results = MODES[mode](conn, Query(case.question, embedding, embedder.model))
            doc_ids = [r.doc_id for r in results]
            outcomes.append(Outcome(case, mode, doc_ids, first_hit_rank(doc_ids, case.expected)))
    return outcomes


def summary_table(outcomes: list[Outcome], modes: list[str]) -> str:
    """Markdown table: one row per mode and group (all, en, uk, each kind)."""
    kinds = sorted({o.case.kind for o in outcomes})
    groups: list[tuple[str, Callable[[Case], bool]]] = [
        ("all", lambda c: True),
        ("en", lambda c: c.lang == "en"),
        ("uk", lambda c: c.lang == "uk"),
    ] + [(f"kind={k}", lambda c, k=k: c.kind == k) for k in kinds]

    metrics = [f"hit@{d}" for d in HIT_DEPTHS] + [f"MRR@{K}"]
    lines = [
        "| mode | group | n | " + " | ".join(metrics) + " |",
        "|---|---|---:|" + "---:|" * len(metrics),
    ]
    for mode in modes:
        for name, keep in groups:
            ranks = [o.rank for o in outcomes if o.mode == mode and keep(o.case)]
            values = summarize(ranks)
            cells = " | ".join(f"{values[m]:.2f}" for m in metrics)
            lines.append(f"| {mode} | {name} | {len(ranks)} | {cells} |")
    return "\n".join(lines)


def misses_section(outcomes: list[Outcome]) -> str:
    """Questions with no hit at rank 1, with what was returned instead."""
    lines = [
        "| mode | id | lang | rank | question | expected | top-3 returned |",
        "|---|---|---|---:|---|---|---|",
    ]
    for o in outcomes:
        if o.rank == 1:
            continue
        rank = "-" if o.rank is None else str(o.rank)
        expected = ", ".join(sorted(o.case.expected))
        lines.append(
            f"| {o.mode} | {o.case.id} | {o.case.lang} | {rank} | {o.case.question} "
            f"| {expected} | {', '.join(o.doc_ids[:3])} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--label", required=True, help="report name, e.g. baseline")
    parser.add_argument("--modes", nargs="+", choices=list(MODES), default=list(MODES))
    args = parser.parse_args()

    settings = get_settings()
    if settings.openai_api_key is None:
        print("OPENAI_API_KEY is not set in .env", file=sys.stderr)
        return 1
    client = OpenAI(api_key=settings.openai_api_key.get_secret_value())
    embedder = CachedEmbedder(
        OpenAIEmbedder(client, settings.embedding_model, settings.embedding_dimensions),
        settings.embedding_dimensions,
    )
    cases = load_cases()
    with connect() as conn:
        outcomes = run(conn, cases, embedder, args.modes)

    table = summary_table(outcomes, args.modes)
    report = (
        f"# Retrieval eval: {args.label}\n\n"
        f"{len(cases)} questions ({len(cases) // 2} intents x en/uk), top {K} chunks, "
        f"embeddings: {embedder.model}.\n\n## Summary\n\n{table}\n\n"
        f"## Misses (no expected document at rank 1)\n\n{misses_section(outcomes)}\n"
    )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"retrieval_{args.label}.md"
    out.write_text(report, encoding="utf-8")
    # The table is ASCII; questions with Cyrillic go to the file only (Windows console).
    print(table)
    print(f"\nfull report: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
