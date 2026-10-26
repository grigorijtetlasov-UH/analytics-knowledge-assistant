import psycopg
import pytest

from app.docs import load_documents
from app.ingest import ingest
from app.migrate import migrate
from app.retrieval import (
    SearchResult,
    or_query,
    rrf_merge,
    search_fulltext,
    search_hybrid,
    search_vector,
)
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


# --- unit tests: no database ---


def result(chunk_id: int, doc_id: str = "doc") -> SearchResult:
    return SearchResult(chunk_id, doc_id, "Name", "Section", "content", 0.0)


def test_or_query_keeps_letters_and_digits_only() -> None:
    assert or_query("Як порахувати ДРР?") == "як | порахувати | дрр"
    assert or_query("What's AOV & CAC (2018)?") == "what | s | aov | cac | 2018"
    assert or_query("ad_spend_share") == "ad | spend | share"


def test_or_query_dedupes_and_handles_empty_input() -> None:
    assert or_query("GMV gmv GMV") == "gmv"
    assert or_query("?! ...") == ""


def test_rrf_rewards_chunks_found_by_both_methods() -> None:
    merged = rrf_merge(
        {"vector": [result(1), result(2), result(3)], "fulltext": [result(3), result(4)]},
        k=3,
    )
    # chunk 3: 1/63 + 1/61 beats chunk 1: 1/61 alone
    assert [r.chunk_id for r in merged] == [3, 1, 2]
    assert merged[0].ranks == {"vector": 3, "fulltext": 1}
    assert merged[0].score == pytest.approx(1 / 63 + 1 / 61)


def test_rrf_with_one_empty_list_keeps_the_other_order() -> None:
    merged = rrf_merge({"vector": [result(5), result(7)], "fulltext": []}, k=5)
    assert [r.chunk_id for r in merged] == [5, 7]


# --- integration: full-text and hybrid SQL ---


@pytest.mark.db
def test_fulltext_finds_cyrillic_alias(indexed_conn: psycopg.Connection) -> None:
    # Only the term itself: common words like "що" also occur in some aliases
    # ("що вважаємо замовленням") and would add unrelated documents.
    results = search_fulltext(indexed_conn, "ДРР?", k=20)
    # "ДРР" is ambiguous in everyday speech, so both metrics carry it as an alias.
    assert {r.doc_id for r in results} == {"ad_spend_share", "acos"}


@pytest.mark.db
def test_fulltext_uses_english_stemming(indexed_conn: psycopg.Connection) -> None:
    # "deliveries" is stemmed to "deliveri", matching "delivery" in the documents.
    results = search_fulltext(indexed_conn, "late deliveries", k=10)
    assert "on_time_delivery_rate" in {r.doc_id for r in results}


@pytest.mark.db
def test_fulltext_with_no_matching_words_returns_nothing(indexed_conn: psycopg.Connection) -> None:
    assert search_fulltext(indexed_conn, "xyzzy plugh") == []
    assert search_fulltext(indexed_conn, "?!") == []


@pytest.mark.db
def test_hybrid_returns_k_unique_chunks_with_ranks(indexed_conn: psycopg.Connection) -> None:
    results = search_hybrid(indexed_conn, "ДРР", FakeEmbedder.vector("ДРР"), "fake-model", k=5)
    assert len(results) == 5
    assert len({r.chunk_id for r in results}) == 5
    # Fake vectors are random, so the full-text hits (ad_spend_share, acos) must lead.
    assert results[0].doc_id in {"ad_spend_share", "acos"}
    assert "fulltext" in results[0].ranks
