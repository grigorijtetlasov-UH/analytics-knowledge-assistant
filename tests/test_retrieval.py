import psycopg
import pytest

from app.docs import load_documents
from app.ingest import ingest
from app.migrate import migrate
from app.retrieval import search_vector
from tests.fakes import FakeEmbedder

# Fake embeddings are random: these tests check that the SQL works (ordering, limit,
# model filter, joined fields), not search quality. Quality is measured by evals/run_evals.py.


@pytest.fixture
def indexed_conn(db_conn: psycopg.Connection) -> psycopg.Connection:
    migrate(db_conn)
    ingest(db_conn, load_documents(), FakeEmbedder())
    return db_conn


@pytest.mark.db
def test_chunk_vector_finds_that_chunk_first(indexed_conn: psycopg.Connection) -> None:
    chunk_id, content = indexed_conn.execute(
        "SELECT id, content FROM rag.chunks WHERE doc_id = 'aov' AND section = 'Formula'"
    ).fetchone()

    results = search_vector(indexed_conn, FakeEmbedder.vector(content), "fake-model", k=3)

    assert len(results) == 3
    top = results[0]
    assert (top.chunk_id, top.doc_id, top.name, top.section) == (
        chunk_id,
        "aov",
        "Average Order Value",
        "Formula",
    )
    assert top.score == pytest.approx(1.0, abs=1e-5)
    assert [r.score for r in results] == sorted((r.score for r in results), reverse=True)


@pytest.mark.db
def test_other_model_is_excluded(indexed_conn: psycopg.Connection) -> None:
    assert search_vector(indexed_conn, FakeEmbedder.vector("x"), "another-model") == []
