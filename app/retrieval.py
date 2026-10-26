"""Search the indexed metric documents (rag.chunks).

Every search returns chunks with the document id, name and section, so answers can cite
their sources.
"""

from dataclasses import dataclass

import psycopg

from app.embeddings import vector_literal

DEFAULT_K = 5


@dataclass(frozen=True)
class SearchResult:
    chunk_id: int
    doc_id: str
    name: str  # document name, e.g. "Average Order Value"
    section: str  # e.g. "Formula"
    content: str
    score: float  # higher is better; meaning depends on the search method


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
