from collections.abc import Iterator

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.api import app, get_embedder, get_llm
from app.config import Settings, get_settings
from app.docs import load_documents
from app.ingest import ingest
from app.llm import AnswerStatus, LLMError, LLMResult, ModelAnswer
from app.migrate import migrate
from tests.fakes import FakeEmbedder, FakeLLM

# The API runs against a throwaway database with fake embeddings and a fake LLM:
# these tests check the HTTP contract and error mapping, not answer quality.

ANSWER = ModelAnswer(
    status=AnswerStatus.ANSWERED,
    answer="AOV = GMV / orders [S1]",
    clarifying_question=None,
    source_ids=[1],
)


class FailingLLM:
    model = "claude-opus-5-5"

    def __init__(self, error: Exception) -> None:
        self.error = error

    def answer(self, system: str, user: str) -> LLMResult:
        raise self.error


@pytest.fixture
def api_settings(temp_db_settings: Settings) -> Settings:
    # No API keys: endpoints must not reach real services. "fake-model" matches FakeEmbedder.
    return temp_db_settings.model_copy(
        update={"embedding_model": "fake-model", "openai_api_key": None, "anthropic_api_key": None}
    )


@pytest.fixture
def client(api_settings: Settings, db_conn: psycopg.Connection) -> Iterator[TestClient]:
    migrate(db_conn)
    ingest(db_conn, load_documents(), FakeEmbedder())
    app.dependency_overrides[get_settings] = lambda: api_settings
    app.dependency_overrides[get_embedder] = FakeEmbedder
    app.dependency_overrides[get_llm] = lambda: FakeLLM(ANSWER)
    yield TestClient(app)
    app.dependency_overrides.clear()


def on_topic_question(conn: psycopg.Connection) -> str:
    """Text whose fake embedding equals the AOV Formula chunk's (similarity 1.0)."""
    return conn.execute(
        "SELECT content FROM rag.chunks WHERE doc_id = 'aov' AND section = 'Formula'"
    ).fetchone()[0]


@pytest.mark.db
def test_ask_returns_answer_with_sources_and_cost(
    client: TestClient, db_conn: psycopg.Connection
) -> None:
    response = client.post("/ask", json={"question": on_topic_question(db_conn)})

    assert response.status_code == 200
    assert response.json() == {
        "status": "answered",
        "answer": "AOV = GMV / orders [S1]",
        "clarifying_question": None,
        "sources": [{"doc_id": "aov", "name": "Average Order Value", "section": "Formula"}],
        "model": "claude-opus-5-5",
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 200,
            "cache_read_input_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cost_usd": 0.008,
        },
    }


@pytest.mark.db
def test_off_topic_question_has_no_model_and_no_usage(client: TestClient) -> None:
    response = client.post("/ask", json={"question": "Як приготувати борщ?"})
    body = response.json()
    assert response.status_code == 200
    assert body["status"] == "off_topic"
    assert body["sources"] == []
    assert body["model"] is None and body["usage"] is None


@pytest.mark.db
def test_invented_source_is_an_error_not_an_answer(
    client: TestClient, db_conn: psycopg.Connection
) -> None:
    bad = ANSWER.model_copy(update={"source_ids": [9]})
    app.dependency_overrides[get_llm] = lambda: FakeLLM(bad)
    response = client.post("/ask", json={"question": on_topic_question(db_conn)})
    assert response.status_code == 502
    assert "invalid answer" in response.json()["detail"]


@pytest.mark.db
@pytest.mark.parametrize(("retryable", "status_code"), [(True, 503), (False, 502)])
def test_llm_errors_map_to_http_status(
    client: TestClient, db_conn: psycopg.Connection, retryable: bool, status_code: int
) -> None:
    error = LLMError("boom", retryable=retryable)
    app.dependency_overrides[get_llm] = lambda: FailingLLM(error)
    response = client.post("/ask", json={"question": on_topic_question(db_conn)})
    assert response.status_code == status_code


@pytest.mark.db
def test_missing_anthropic_key_is_503(client: TestClient) -> None:
    del app.dependency_overrides[get_llm]  # the real dependency, with no key in settings
    response = client.post("/ask", json={"question": "What is AOV?"})
    assert response.status_code == 503
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


@pytest.mark.db
@pytest.mark.parametrize("question", ["", "x" * 1001])
def test_question_length_is_validated(client: TestClient, question: str) -> None:
    assert client.post("/ask", json={"question": question}).status_code == 422


@pytest.mark.db
def test_health_reports_indexed_chunks(client: TestClient, db_conn: psycopg.Connection) -> None:
    [chunks] = db_conn.execute("SELECT count(*) FROM rag.chunks").fetchone()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "chunks": chunks}


def test_health_is_503_when_database_is_down() -> None:
    # Port 1 on localhost: nothing listens there, so the connection is refused at once.
    # No database needed, so this test runs everywhere.
    settings = Settings(
        _env_file=None,
        postgres_user="u",
        postgres_password="p",
        postgres_db="d",
        postgres_port=1,
    )
    app.dependency_overrides[get_settings] = lambda: settings
    try:
        response = TestClient(app).get("/health")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json() == {"detail": "database unavailable"}


@pytest.mark.db
def test_health_is_503_when_not_migrated(api_settings: Settings) -> None:
    app.dependency_overrides[get_settings] = lambda: api_settings
    try:
        response = TestClient(app).get("/health")
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert "not migrated" in response.json()["detail"]
