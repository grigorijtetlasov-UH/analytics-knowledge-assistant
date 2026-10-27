"""MCP server: the metric docs and the Olist data as tools for Claude Desktop / Claude Code.

Run (stdio transport; the MCP client starts this process itself):
    uv run python -m mcp_server.server

Tools:
- search_docs(query, k): vector search over the metric docs, chunks with sources;
- get_metric_definition(name): exact lookup by id, name or alias, with formula and SQL;
- run_readonly_sql(query): one SELECT on the olist schema as the read-only role.

Unlike /ask, this server calls no LLM: the client's model (Claude in Desktop) reads the
tool results and writes the answer itself.

stdout carries the MCP protocol, so nothing else may print there: logs go to stderr.
"""

import difflib
import logging
import sys
from collections.abc import Callable
from typing import Annotated, Literal

import psycopg
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp_types import ToolAnnotations
from openai import OpenAI
from pydantic import BaseModel, Field

from app.config import Settings, get_settings
from app.db import connect, connect_readonly
from app.embeddings import Embedder, OpenAIEmbedder
from app.readonly_sql import SqlError, run_readonly_sql
from app.retrieval import search_vector

logger = logging.getLogger(__name__)

# Sections returned by get_metric_definition; Interpretation and Pitfalls come via search_docs.
DEFINITION_SECTIONS = ("Definition", "Formula", "Calculation on Olist data")
# All three tools only read. Clients such as Claude Desktop show this to the user.
READ_ONLY = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True)

INSTRUCTIONS = """\
Tools for questions about e-commerce metrics and the Olist Brazilian e-commerce dataset.
- Start with get_metric_definition when the question names a metric (an id, name or alias
  such as "AOV", "LTV", "ДРР"); use search_docs for paraphrased questions or details.
- If get_metric_definition returns status "ambiguous" (e.g. "ДРР" means ad spend share or
  ACoS), explain every candidate and ask which one is meant; do not guess.
- For numbers, run the SQL from the metric's "Calculation on Olist data" section with
  run_readonly_sql, adapted to the question (period, grouping). Only SELECT on the olist
  schema is allowed; results are capped at 100 rows and 5 seconds.
- Metrics with data_availability "none" cannot be calculated from Olist; say what data is
  missing instead of approximating.
"""


class DocChunk(BaseModel):
    doc_id: str
    name: str
    section: str
    score: float  # cosine similarity, 1 = identical
    content: str


class MetricDefinition(BaseModel):
    id: str
    name: str
    aliases: list[str]
    data_availability: str  # full | partial | none
    sections: dict[str, str]  # Definition, Formula, Calculation on Olist data
    related: list[str]


class MetricLookup(BaseModel):
    # found: one metric; ambiguous: the name fits several (explain all, ask which);
    # not_found: see suggestions, or use search_docs.
    status: Literal["found", "ambiguous", "not_found"]
    metrics: list[MetricDefinition]
    suggestions: list[str]


class SqlOutput(BaseModel):
    columns: list[str]
    rows: list[list[str | int | float | bool | None]]
    row_count: int
    truncated: bool  # more rows exist than the 100 returned
    elapsed_ms: int


def chunk_body(content: str) -> str:
    """A stored chunk starts with a header line ("Name (id; also: ...) — Section") added for
    retrieval (app/docs.py); the tool output already has these as fields."""
    _, _, body = content.partition("\n\n")
    return body or content


def lookup_metric(conn: psycopg.Connection, name: str) -> MetricLookup:
    """Case-insensitive exact match on id, name or any alias."""
    key = name.strip().casefold()
    documents = conn.execute("SELECT id, metadata FROM rag.documents ORDER BY id").fetchall()
    matches = [
        (doc_id, meta)
        for doc_id, meta in documents
        if key
        in {doc_id.casefold(), meta["name"].casefold()}
        | {alias.casefold() for alias in meta.get("aliases", [])}
    ]
    if not matches:
        names = [n for doc_id, meta in documents for n in (doc_id, meta["name"])]
        suggestions = difflib.get_close_matches(name, names, n=3, cutoff=0.5)
        return MetricLookup(status="not_found", metrics=[], suggestions=suggestions)

    rows = conn.execute(
        "SELECT doc_id, section, content FROM rag.chunks"
        " WHERE doc_id = ANY(%s) AND section = ANY(%s) ORDER BY doc_id, chunk_index",
        ([doc_id for doc_id, _ in matches], list(DEFINITION_SECTIONS)),
    ).fetchall()
    sections: dict[str, dict[str, str]] = {}
    for doc_id, section, content in rows:
        sections.setdefault(doc_id, {})[section] = chunk_body(content)
    metrics = [
        MetricDefinition(
            id=doc_id,
            name=meta["name"],
            aliases=meta.get("aliases", []),
            data_availability=meta["data_availability"],
            sections=sections.get(doc_id, {}),
            related=meta.get("related", []),
        )
        for doc_id, meta in matches
    ]
    status = "found" if len(metrics) == 1 else "ambiguous"
    return MetricLookup(status=status, metrics=metrics, suggestions=[])


def create_server(settings: Settings, make_embedder: Callable[[], Embedder]) -> MCPServer:
    """Build the server. Tests pass a throwaway database and a fake embedder."""
    server = MCPServer(name="analytics", instructions=INSTRUCTIONS)

    def open_db() -> psycopg.Connection:
        try:
            return connect(settings, autocommit=True)
        except psycopg.OperationalError as exc:
            logger.error("database unavailable: %s", exc)
            raise ToolError("database unavailable; is `docker compose up -d` running?") from exc

    @server.tool(annotations=READ_ONLY)
    def search_docs(
        query: Annotated[str, Field(min_length=1, max_length=1000)],
        k: Annotated[int, Field(ge=1, le=10)] = 5,
    ) -> list[DocChunk]:
        """Semantic search over the metric documentation (definitions, formulas, SQL,
        pitfalls). Returns the k most similar sections with their source document."""
        embedder = make_embedder()
        [embedding] = embedder.embed([query])
        with open_db() as conn:
            results = search_vector(conn, embedding, embedder.model, k)
        return [
            DocChunk(
                doc_id=r.doc_id,
                name=r.name,
                section=r.section,
                score=round(r.score, 3),
                content=chunk_body(r.content),
            )
            for r in results
        ]

    @server.tool(annotations=READ_ONLY)
    def get_metric_definition(
        name: Annotated[str, Field(min_length=1, max_length=200)],
    ) -> MetricLookup:
        """Exact definition, formula and Olist SQL of a metric, looked up by id ("aov"),
        name ("Average Order Value") or alias ("AOV", "середній чек", "ДРР"), ignoring case.
        status "ambiguous" means the name fits several metrics."""
        with open_db() as conn:
            return lookup_metric(conn, name)

    @server.tool(name="run_readonly_sql", annotations=READ_ONLY)
    def run_sql(query: Annotated[str, Field(min_length=1)]) -> SqlOutput:
        """Run exactly one SELECT against the Olist tables (schema olist: orders,
        order_items, customers, products, sellers, order_payments, order_reviews, ...).
        Read-only role; at most 100 rows and 5 seconds. Anything else is rejected by the
        database, and the error text says why."""
        if settings.readonly_db_password is None:
            raise ToolError("the SQL tool is disabled: READONLY_DB_PASSWORD is not set")
        try:
            with connect_readonly(settings) as conn:
                result = run_readonly_sql(
                    conn, query, max_rows=settings.sql_max_rows, timeout_ms=settings.sql_timeout_ms
                )
        except psycopg.OperationalError as exc:
            logger.error("read-only connection failed: %s", exc)
            raise ToolError("database unavailable for the read-only role") from exc
        except SqlError as exc:
            logger.info("query rejected: %s", exc)
            raise ToolError(str(exc)) from exc
        return SqlOutput(
            columns=result.columns,
            rows=result.rows,
            row_count=result.row_count,
            truncated=result.truncated,
            elapsed_ms=result.elapsed_ms,
        )

    return server


def openai_embedder(settings: Settings) -> Callable[[], Embedder]:
    """Created on first use, so the server starts (and the other tools work) without a key."""
    cache: list[Embedder] = []

    def make() -> Embedder:
        if settings.openai_api_key is None:
            raise ToolError("search_docs is disabled: OPENAI_API_KEY is not set")
        if not cache:
            client = OpenAI(api_key=settings.openai_api_key.get_secret_value())
            cache.append(
                OpenAIEmbedder(client, settings.embedding_model, settings.embedding_dimensions)
            )
        return cache[0]

    return make


def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    settings = get_settings()
    create_server(settings, openai_embedder(settings)).run("stdio")


if __name__ == "__main__":
    main()
