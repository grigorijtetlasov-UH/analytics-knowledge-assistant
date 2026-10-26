"""Embed the metric documents and store them in rag.documents / rag.chunks.

Usage: uv run python -m app.ingest [--docs-dir data/docs] [--dry-run]

Idempotent and incremental:
- a document whose file and embedding model did not change is skipped;
- a changed document has its chunks replaced, but a chunk whose text already has an
  embedding (same content hash, same model) reuses it, so editing one section of a
  document calls the API for that one section only;
- documents whose files were deleted are removed from the index.
All database changes happen in one transaction; the API is called before it starts, so no
database lock is held while waiting on the network.
"""

import argparse
import hashlib
import sys
from dataclasses import dataclass
from pathlib import Path

import openai
import psycopg
from openai import OpenAI
from psycopg.types.json import Jsonb

from app.config import get_settings
from app.db import connect
from app.docs import DEFAULT_DOCS_DIR, Chunk, DocError, Document, chunk_document, load_documents
from app.embeddings import Embedder, OpenAIEmbedder


@dataclass(frozen=True)
class IngestStats:
    documents: int  # documents in the docs directory
    changed: int  # new or modified documents (re)written
    deleted: int  # documents removed from the index
    chunks_embedded: int  # texts sent to the embeddings API
    chunks_reused: int  # chunks of changed documents that reused a stored embedding


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def vector_literal(vector: list[float]) -> str:
    """pgvector's text format, '[0.1,0.2,...]'. Sending vectors as text with a ::vector cast
    avoids an extra dependency (pgvector-python + numpy) for a few hundred rows."""
    return "[" + ",".join(repr(x) for x in vector) + "]"


def changed_documents(
    conn: psycopg.Connection, documents: list[Document], model: str
) -> list[Document]:
    """Documents that are new, edited, or were embedded with a different model."""
    rows = conn.execute(
        """
        SELECT d.id, d.content_hash, bool_and(c.embedding_model = %s)
        FROM rag.documents AS d
        LEFT JOIN rag.chunks AS c ON c.doc_id = d.id
        GROUP BY d.id
        """,
        (model,),
    ).fetchall()
    up_to_date = {doc_id for doc_id, file_hash, same_model in rows if same_model}
    stored_hash = {doc_id: file_hash for doc_id, file_hash, _ in rows}
    return [
        d
        for d in documents
        if d.meta.id not in up_to_date or stored_hash[d.meta.id] != d.content_hash
    ]


def deleted_document_ids(conn: psycopg.Connection, documents: list[Document]) -> list[str]:
    current = {d.meta.id for d in documents}
    stored = [doc_id for (doc_id,) in conn.execute("SELECT id FROM rag.documents ORDER BY id")]
    return [doc_id for doc_id in stored if doc_id not in current]


def stored_embeddings(conn: psycopg.Connection, hashes: list[str], model: str) -> dict[str, str]:
    """content hash -> embedding (pgvector text) for texts already embedded with `model`."""
    rows = conn.execute(
        """
        SELECT DISTINCT ON (content_hash) content_hash, embedding::text
        FROM rag.chunks
        WHERE content_hash = ANY(%s) AND embedding_model = %s
        """,
        (hashes, model),
    ).fetchall()
    return dict(rows)


def write_document(
    conn: psycopg.Connection,
    document: Document,
    chunks: list[Chunk],
    vectors: dict[str, str],
    model: str,
) -> None:
    conn.execute(
        """
        INSERT INTO rag.documents (id, name, metadata, content_hash)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE
        SET name = EXCLUDED.name, metadata = EXCLUDED.metadata,
            content_hash = EXCLUDED.content_hash, updated_at = now()
        """,
        (
            document.meta.id,
            document.meta.name,
            Jsonb(document.meta.model_dump(mode="json")),
            document.content_hash,
        ),
    )
    # Replace all chunks: simpler than diffing, and cheap because embeddings are reused.
    conn.execute("DELETE FROM rag.chunks WHERE doc_id = %s", (document.meta.id,))
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO rag.chunks
                (doc_id, chunk_index, section, content, content_hash, embedding, embedding_model)
            VALUES (%s, %s, %s, %s, %s, %s::vector, %s)
            """,
            [
                (
                    c.doc_id,
                    c.index,
                    c.section,
                    c.content,
                    content_hash(c.content),
                    vectors[content_hash(c.content)],
                    model,
                )
                for c in chunks
            ],
        )


def ingest(
    conn: psycopg.Connection,
    documents: list[Document],
    embedder: Embedder,
    *,
    dry_run: bool = False,
) -> IngestStats:
    """Bring rag.* in line with `documents`. `conn` must be in autocommit mode."""
    changed = changed_documents(conn, documents, embedder.model)
    deleted = deleted_document_ids(conn, documents)
    chunks = {d.meta.id: chunk_document(d) for d in changed}

    # Unique texts only: identical chunks share one embedding.
    texts = {content_hash(c.content): c.content for cs in chunks.values() for c in cs}
    vectors = stored_embeddings(conn, list(texts), embedder.model)
    missing = [h for h in texts if h not in vectors]
    stats = IngestStats(
        documents=len(documents),
        changed=len(changed),
        deleted=len(deleted),
        chunks_embedded=len(missing),
        chunks_reused=sum(len(cs) for cs in chunks.values()) - len(missing),
    )
    if dry_run:
        return stats

    new_vectors = embedder.embed([texts[h] for h in missing])
    vectors.update(zip(missing, map(vector_literal, new_vectors), strict=True))

    with conn.transaction():
        # ON DELETE CASCADE removes the chunks of deleted documents.
        conn.execute("DELETE FROM rag.documents WHERE id = ANY(%s)", (deleted,))
        for document in changed:
            write_document(conn, document, chunks[document.meta.id], vectors, embedder.model)
    return stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--docs-dir", type=Path, default=DEFAULT_DOCS_DIR)
    parser.add_argument(
        "--dry-run", action="store_true", help="show what would change; no API calls, no writes"
    )
    args = parser.parse_args()

    settings = get_settings()
    if settings.openai_api_key is None:
        print("OPENAI_API_KEY is not set in .env", file=sys.stderr)
        return 1
    try:
        documents = load_documents(args.docs_dir)
    except DocError as exc:
        print(f"invalid document: {exc}", file=sys.stderr)
        return 1
    if not documents:
        # Guard: with an empty or wrong --docs-dir, ingest would delete the whole index.
        print(f"no *.md documents in {args.docs_dir}", file=sys.stderr)
        return 1

    client = OpenAI(api_key=settings.openai_api_key.get_secret_value())
    embedder = OpenAIEmbedder(client, settings.embedding_model, settings.embedding_dimensions)
    try:
        with connect(autocommit=True) as conn:
            stats = ingest(conn, documents, embedder, dry_run=args.dry_run)
    except openai.APIError as exc:
        # Raised before the database transaction starts, so the index is unchanged.
        print(f"embeddings API error, index not changed: {exc}", file=sys.stderr)
        return 1

    # ASCII only: the Windows console (cp1251) cannot print every Unicode character.
    prefix = "[dry run] " if args.dry_run else ""
    print(
        f"{prefix}documents: {stats.documents} (changed {stats.changed}, deleted {stats.deleted})"
    )
    print(f"{prefix}chunks: embedded {stats.chunks_embedded}, reused {stats.chunks_reused}")
    if embedder.total_tokens:
        print(f"tokens: {embedder.total_tokens} ({embedder.model})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
