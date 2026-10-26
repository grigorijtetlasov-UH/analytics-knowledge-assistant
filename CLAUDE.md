# Analytics Knowledge Assistant

Portfolio project. A RAG assistant that answers business questions about e-commerce metrics
and data, exposed both as a REST API and as an MCP server, with an evaluation suite.

Goal: a public GitHub repo that shows RAG, tool use, MCP, evals and production skills.
The owner must understand every line. Explain non-obvious decisions in comments and in the PR/commit message.

## Stack
- Python 3.11+, FastAPI, Pydantic
- PostgreSQL 16 + pgvector (Docker Compose)
- LLM: Anthropic Claude API; embeddings: OpenAI `text-embedding-3-small` (configurable)
- MCP: official Python SDK (`mcp`, FastMCP)
- Evals: pytest + a JSON test set; LLM-as-judge for answer correctness
- Tracing: Langfuse (optional, behind an env flag)
- Tooling: uv, ruff, pytest, GitHub Actions

## Data (IMPORTANT)
- Never use real company data (United Home, CRM, 1C). The repo is public.
- Structured data: public Olist Brazilian E-commerce dataset (Kaggle), loaded into Postgres.
- Documents: `data/docs/*.md` — metric definitions and business rules written for this project
  (conversion, AOV, ad-spend share / ACoS, cross-sell rate, refusal rate, unit economics, etc.).

## Architecture
```
data/docs/*.md ──ingest──> chunks + embeddings ──> pgvector
Olist CSV ──load──> Postgres tables
                    │
        retrieval (vector + keyword hybrid)
                    │
   ┌────────────────┼────────────────┐
FastAPI /ask     MCP server       evals/
(answer + sources) (tools)        (test set + metrics)
```

MCP tools:
- `search_docs(query, k)` — hybrid search over metric docs, returns chunks with sources
- `get_metric_definition(name)` — exact definition + formula
- `run_readonly_sql(query)` — SELECT-only, read-only DB role, row limit, timeout

## Layout
```
app/        api.py, retrieval.py, llm.py, ingest.py, db.py, config.py
mcp_server/ server.py
evals/      testset.json, run_evals.py, test_retrieval.py
data/docs/  metric definition markdown files
migrations/ numbered plain-SQL files (NNN_name.sql), applied in order by app/migrate.py
docker-compose.yml, pyproject.toml, .env.example, README.md
```

## Milestones (do them in order, one PR/commit series each)
1. Docker Compose with Postgres + pgvector; schema migrations; load Olist data.
2. Write 10–15 metric docs; ingestion: chunking, embeddings, upsert (idempotent re-runs).
3. Retrieval: vector search, then hybrid (pgvector + Postgres full-text), return sources.
4. `/ask` endpoint: retrieve → prompt with context → answer with cited sources.
5. MCP server with the three tools; test it from Claude Desktop / Claude Code.
6. Evals: 30+ questions with expected sources/answers; report hit@k, MRR, answer accuracy.
   Run in GitHub Actions on every PR.
7. Langfuse tracing, structured logs, deploy to VPS with Docker; README with diagram,
   eval results table and a short demo GIF.

## Rules
- Secrets only in `.env` (never committed); `.env.example` lists every variable.
- SQL tool: read-only DB role, reject anything that is not a single SELECT.
- Every new feature comes with a test or an eval case.
- Keep functions small and typed; ruff must pass.
- Before writing code for a milestone, propose a short plan and wait for approval.
- Communicate with me in Ukrainian. Keep code, comments, commit messages, README and docs in English.
