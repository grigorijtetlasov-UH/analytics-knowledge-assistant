"""The MCP server, tested through the MCP protocol with the SDK's in-process client.

Real database (throwaway), fake embeddings, real read-only role. The SQL safety itself is
tested in tests/test_readonly_sql.py; here only that the tool wires it up and reports
rejections as tool errors the model can read.
"""

import asyncio
from typing import Any

import psycopg
import pytest
from mcp import Client
from mcp_types import CallToolResult

from app.config import Settings
from app.docs import load_documents
from app.ingest import ingest
from app.migrate import migrate, set_readonly_password
from mcp_server.server import chunk_body, create_server
from tests.fakes import FakeEmbedder

TOOLS = {"search_docs", "get_metric_definition", "run_readonly_sql"}


@pytest.fixture
def server_settings(temp_db_settings: Settings, db_conn: psycopg.Connection) -> Settings:
    if temp_db_settings.readonly_db_password is None:
        pytest.skip("READONLY_DB_PASSWORD is not set")
    migrate(db_conn)
    ingest(db_conn, load_documents(), FakeEmbedder())
    set_readonly_password(
        db_conn,
        temp_db_settings.readonly_db_user,
        temp_db_settings.readonly_db_password.get_secret_value(),
    )
    return temp_db_settings


def call(settings: Settings, tool: str, arguments: dict[str, Any]) -> CallToolResult:
    async def go() -> CallToolResult:
        async with Client(create_server(settings, FakeEmbedder)) as client:
            return await client.call_tool(tool, arguments)

    return asyncio.run(go())


def text(result: CallToolResult) -> str:
    return " ".join(block.text for block in result.content if block.type == "text")


@pytest.mark.db
def test_lists_three_read_only_tools(server_settings: Settings) -> None:
    async def go() -> Any:
        async with Client(create_server(server_settings, FakeEmbedder)) as client:
            return await client.list_tools()

    tools = asyncio.run(go()).tools
    assert {t.name for t in tools} == TOOLS
    assert all(t.annotations and t.annotations.read_only_hint for t in tools)
    assert all(t.description for t in tools)


@pytest.mark.db
def test_get_metric_definition_by_alias(server_settings: Settings) -> None:
    result = call(server_settings, "get_metric_definition", {"name": "середній чек"})
    assert not result.is_error
    lookup = result.structured_content
    assert lookup["status"] == "found"
    [metric] = lookup["metrics"]
    assert metric["id"] == "aov"
    assert metric["data_availability"] == "full"
    assert set(metric["sections"]) == {"Definition", "Formula", "Calculation on Olist data"}
    assert "SELECT" in metric["sections"]["Calculation on Olist data"]
    # The retrieval header line is stripped from the section text.
    assert not metric["sections"]["Formula"].startswith("Average Order Value (aov")


@pytest.mark.db
@pytest.mark.parametrize("name", ["ДРР", "drr", "DRR"])
def test_drr_is_ambiguous(server_settings: Settings, name: str) -> None:
    lookup = call(server_settings, "get_metric_definition", {"name": name}).structured_content
    assert lookup["status"] == "ambiguous"
    assert {m["id"] for m in lookup["metrics"]} == {"acos", "ad_spend_share"}


@pytest.mark.db
def test_unknown_metric_gets_suggestions(server_settings: Settings) -> None:
    lookup = call(server_settings, "get_metric_definition", {"name": "Average Order Valu"})
    assert lookup.structured_content["status"] == "not_found"
    assert "Average Order Value" in lookup.structured_content["suggestions"]


@pytest.mark.db
def test_search_docs_returns_sources(
    server_settings: Settings, db_conn: psycopg.Connection
) -> None:
    [content] = db_conn.execute(
        "SELECT content FROM rag.chunks WHERE doc_id = 'cac' AND section = 'Formula'"
    ).fetchone()
    # FakeEmbedder: a query equal to the chunk text has similarity 1.0 with it.
    result = call(server_settings, "search_docs", {"query": content, "k": 3})
    chunks = result.structured_content["result"]
    assert len(chunks) == 3
    assert chunks[0] == {
        "doc_id": "cac",
        "name": "Customer Acquisition Cost",
        "section": "Formula",
        "score": 1.0,
        "content": chunk_body(content),
    }


@pytest.mark.db
def test_search_docs_validates_k(server_settings: Settings) -> None:
    result = call(server_settings, "search_docs", {"query": "AOV", "k": 50})
    assert result.is_error


@pytest.mark.db
def test_run_readonly_sql(server_settings: Settings) -> None:
    result = call(
        server_settings, "run_readonly_sql", {"query": "SELECT count(*) AS n FROM orders"}
    )
    assert not result.is_error
    assert result.structured_content == {
        "columns": ["n"],
        "rows": [[0]],
        "row_count": 1,
        "truncated": False,
        "elapsed_ms": result.structured_content["elapsed_ms"],
    }


@pytest.mark.db
@pytest.mark.parametrize(
    ("query", "message"),
    [
        ("DROP TABLE olist.orders", 'syntax error at or near "DROP"'),
        ("SELECT * FROM rag.chunks", "permission denied for schema rag"),
    ],
)
def test_rejected_sql_is_a_readable_tool_error(
    server_settings: Settings, query: str, message: str
) -> None:
    result = call(server_settings, "run_readonly_sql", {"query": query})
    assert result.is_error
    assert message in text(result)


@pytest.mark.db
def test_sql_tool_is_disabled_without_password(server_settings: Settings) -> None:
    settings = server_settings.model_copy(update={"readonly_db_password": None})
    result = call(settings, "run_readonly_sql", {"query": "SELECT 1"})
    assert result.is_error
    assert "READONLY_DB_PASSWORD" in text(result)
