"""Search the indexed metric documents (rag.chunks).

Three methods:
- search_vector: semantic similarity of embeddings; finds paraphrases, weak on rare terms;
- search_fulltext: Postgres full-text search; finds exact terms (abbreviations, aliases);
- search_hybrid: both, merged with Reciprocal Rank Fusion.
Every search returns chunks with the document id, name and section, so answers can cite
their sources.
"""

import re
from dataclasses import dataclass, field

import psycopg

from app.embeddings import vector_literal

DEFAULT_K = 5
# How many results each method contributes to the hybrid merge.
HYBRID_CANDIDATES = 20
# The constant from the original RRF paper (Cormack et al., 2009). It dampens the
# difference between rank 1 and rank 2; we keep the standard value instead of tuning it
# on a 30-question test set, which would overfit.
RRF_K = 60


@dataclass(frozen=True)
class SearchResult:
    chunk_id: int
    doc_id: str
    name: str  # document name, e.g. "Average Order Value"
    section: str  # e.g. "Formula"
    content: str
    # Higher is better. vector: cosine similarity; fulltext: ts_rank_cd; hybrid: RRF score.
    score: float
    # Hybrid only: rank of this chunk in each method's list, e.g. {"vector": 1, "fulltext": 4}.
    ranks: dict[str, int] = field(default_factory=dict)


def search_vector(
    conn: psycopg.Connection, embedding: list[float], model: str, k: int = DEFAULT_K
) -> list[SearchResult]:
    """The k chunks closest to the query embedding by cosine distance.

    `model` must be the model that produced `embedding`: chunks embedded with another model
    live in a different vector space and are excluded. Score = cosine similarity (1 is
    identical direction).
    """
    rows = conn.execute(
        """
        SELECT c.id, c.doc_id, d.name, c.section, c.content,
               1 - (c.embedding <=> %(query)s::vector) AS score
        FROM rag.chunks AS c
        JOIN rag.documents AS d ON d.id = c.doc_id
        WHERE c.embedding_model = %(model)s
        ORDER BY c.embedding <=> %(query)s::vector
        LIMIT %(k)s
        """,
        {"query": vector_literal(embedding), "model": model, "k": k},
    ).fetchall()
    return [SearchResult(*row) for row in rows]


def or_query(text: str) -> str:
    """Turn a question into a tsquery string that matches ANY of its words: 'a | b | c'.

    Postgres' websearch_to_tsquery() requires ALL words to match, so "Як порахувати ДРР?"
    would find nothing: "як" and "порахувати" appear in no document. Only letters and digits
    are kept, so the result is always valid tsquery syntax.
    """
    words = re.findall(r"[^\W_]+", text.lower())
    return " | ".join(dict.fromkeys(words))  # dict.fromkeys: dedupe, keep order


def search_fulltext(conn: psycopg.Connection, text: str, k: int = DEFAULT_K) -> list[SearchResult]:
    """The k chunks with the best full-text rank for any of the question's words.

    The question is parsed twice, matching the two parts of rag.chunks.tsv: with `simple`
    (exact tokens such as "ДРР" against the header) and with `english` (stemmed words against
    the text). English stop words like "what" or "is" are dropped by the `english` parser.
    """
    query = or_query(text)
    if not query:
        return []
    rows = conn.execute(
        """
        WITH q AS (
            SELECT to_tsquery('simple', %(query)s) || to_tsquery('english', %(query)s) AS query
        )
        SELECT c.id, c.doc_id, d.name, c.section, c.content,
               ts_rank_cd(c.tsv, q.query) AS score
        FROM rag.chunks AS c
        JOIN rag.documents AS d ON d.id = c.doc_id
        CROSS JOIN q
        WHERE c.tsv @@ q.query
        ORDER BY score DESC, c.id
        LIMIT %(k)s
        """,
        {"query": query, "k": k},
    ).fetchall()
    return [SearchResult(*row) for row in rows]


def rrf_merge(ranked_lists: dict[str, list[SearchResult]], k: int) -> list[SearchResult]:
    """Reciprocal Rank Fusion: each chunk scores sum(1 / (RRF_K + rank)) over the lists it
    appears in. Only ranks are used, so the scores of different methods (cosine similarity,
    ts_rank_cd) never need to be put on one scale."""
    scores: dict[int, float] = {}
    ranks: dict[int, dict[str, int]] = {}
    chunks: dict[int, SearchResult] = {}
    for method, results in ranked_lists.items():
        for rank, result in enumerate(results, start=1):
            scores[result.chunk_id] = scores.get(result.chunk_id, 0.0) + 1 / (RRF_K + rank)
            ranks.setdefault(result.chunk_id, {})[method] = rank
            chunks.setdefault(result.chunk_id, result)
    # Ties (same score) are broken by chunk id so the order is deterministic.
    best = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))[:k]
    return [
        SearchResult(
            chunk_id=chunk_id,
            doc_id=chunks[chunk_id].doc_id,
            name=chunks[chunk_id].name,
            section=chunks[chunk_id].section,
            content=chunks[chunk_id].content,
            score=scores[chunk_id],
            ranks=ranks[chunk_id],
        )
        for chunk_id in best
    ]


def search_hybrid(
    conn: psycopg.Connection,
    text: str,
    embedding: list[float],
    model: str,
    k: int = DEFAULT_K,
) -> list[SearchResult]:
    """Vector and full-text search merged with RRF. A chunk found by both methods rises to
    the top; a chunk found by only one still competes on its rank there."""
    return rrf_merge(
        {
            "vector": search_vector(conn, embedding, model, HYBRID_CANDIDATES),
            "fulltext": search_fulltext(conn, text, HYBRID_CANDIDATES),
        },
        k,
    )
