import hashlib
import shutil
from pathlib import Path

import psycopg
import pytest

from app.docs import chunk_document, load_documents
from app.embeddings import vector_literal
from app.ingest import content_hash, ingest
from app.migrate import migrate
from tests.fakes import FakeEmbedder


@pytest.fixture
def docs_dir(tmp_path: Path) -> Path:
    """A writable copy of the real documents."""
    return Path(shutil.copytree("data/docs", tmp_path / "docs"))


@pytest.fixture
def rag_conn(db_conn: psycopg.Connection) -> psycopg.Connection:
    migrate(db_conn)
    return db_conn


def counts(conn: psycopg.Connection) -> tuple[int, int]:
    documents = conn.execute("SELECT count(*) FROM rag.documents").fetchone()[0]
    chunks = conn.execute("SELECT count(*) FROM rag.chunks").fetchone()[0]
    return documents, chunks


# --- unit tests ---


def test_vector_literal_is_pgvector_text_format() -> None:
    assert vector_literal([0.5, -1.0, 2e-05]) == "[0.5,-1.0,2e-05]"


def test_content_hash_is_sha256_hex() -> None:
    assert content_hash("abc") == hashlib.sha256(b"abc").hexdigest()


# --- integration tests: throwaway database, fake embeddings ---


@pytest.mark.db
def test_first_ingest_stores_every_chunk(rag_conn: psycopg.Connection, docs_dir: Path) -> None:
    documents = load_documents(docs_dir)
    total_chunks = sum(len(chunk_document(d)) for d in documents)
    embedder = FakeEmbedder()

    stats = ingest(rag_conn, documents, embedder)

    assert stats.changed == len(documents)
    assert stats.chunks_embedded + stats.chunks_reused == total_chunks
    assert counts(rag_conn) == (len(documents), total_chunks)
    # The stored vector is exactly what the embedder returned for that text.
    content, embedding = rag_conn.execute(
        "SELECT content, embedding::text FROM rag.chunks ORDER BY id LIMIT 1"
    ).fetchone()
    stored = [float(x) for x in embedding.strip("[]").split(",")]
    assert stored == pytest.approx(FakeEmbedder.vector(content), abs=1e-6)


@pytest.mark.db
def test_rerun_without_changes_is_a_no_op(rag_conn: psycopg.Connection, docs_dir: Path) -> None:
    documents = load_documents(docs_dir)
    ingest(rag_conn, documents, FakeEmbedder())
    before = rag_conn.execute("SELECT id, content_hash FROM rag.chunks ORDER BY id").fetchall()

    embedder = FakeEmbedder()
    stats = ingest(rag_conn, documents, embedder)

    assert (stats.changed, stats.deleted, stats.chunks_embedded) == (0, 0, 0)
    assert embedder.embedded == []
    after = rag_conn.execute("SELECT id, content_hash FROM rag.chunks ORDER BY id").fetchall()
    assert after == before


@pytest.mark.db
def test_editing_one_section_embeds_only_that_section(
    rag_conn: psycopg.Connection, docs_dir: Path
) -> None:
    ingest(rag_conn, load_documents(docs_dir), FakeEmbedder())
    path = docs_dir / "gmv.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace("## Interpretation\n", "## Interpretation\n- An added line.\n"),
        encoding="utf-8",
    )

    embedder = FakeEmbedder()
    stats = ingest(rag_conn, load_documents(docs_dir), embedder)

    assert stats.changed == 1
    assert stats.chunks_embedded == 1
    assert embedder.embedded[0].startswith("Gross Merchandise Value (gmv")
    assert "- An added line." in embedder.embedded[0]
    stored = rag_conn.execute(
        "SELECT content FROM rag.chunks WHERE doc_id = 'gmv' AND section = 'Interpretation'"
    ).fetchone()[0]
    assert "- An added line." in stored


@pytest.mark.db
def test_deleted_document_is_removed_with_its_chunks(
    rag_conn: psycopg.Connection, docs_dir: Path
) -> None:
    ingest(rag_conn, load_documents(docs_dir), FakeEmbedder())
    (docs_dir / "acos.md").unlink()
    # Links to the deleted doc are irrelevant here; ingest does not check links.

    stats = ingest(rag_conn, load_documents(docs_dir), FakeEmbedder())

    assert stats.deleted == 1
    assert rag_conn.execute("SELECT count(*) FROM rag.documents WHERE id = 'acos'").fetchone() == (
        0,
    )
    assert rag_conn.execute("SELECT count(*) FROM rag.chunks WHERE doc_id = 'acos'").fetchone() == (
        0,
    )


@pytest.mark.db
def test_switching_model_re_embeds_everything(rag_conn: psycopg.Connection, docs_dir: Path) -> None:
    documents = load_documents(docs_dir)
    ingest(rag_conn, documents, FakeEmbedder("model-a"))

    embedder = FakeEmbedder("model-b")
    stats = ingest(rag_conn, documents, embedder)

    assert stats.changed == len(documents)
    assert stats.chunks_reused == 0
    models = rag_conn.execute("SELECT DISTINCT embedding_model FROM rag.chunks").fetchall()
    assert models == [("model-b",)]


@pytest.mark.db
def test_dry_run_writes_nothing(rag_conn: psycopg.Connection, docs_dir: Path) -> None:
    embedder = FakeEmbedder()
    stats = ingest(rag_conn, load_documents(docs_dir), embedder, dry_run=True)

    assert stats.chunks_embedded > 0
    assert embedder.embedded == []
    assert counts(rag_conn) == (0, 0)
