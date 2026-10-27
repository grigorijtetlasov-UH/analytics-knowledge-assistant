# analytics-knowledge-assistant

A RAG assistant that answers business questions about e-commerce metrics and data,
exposed as a REST API and as an MCP server, with an evaluation suite.

> Work in progress. Done: database, migrations and Olist data (milestone 1); metric
> documents and their ingestion into pgvector (milestone 2); retrieval with measured
> vector vs hybrid search (milestone 3); the `/ask` endpoint with answer evals (milestone 4).

## Retrieval results

15 questions about metrics, each asked in English and Ukrainian ([test set](evals/testset.json));
the metric documents are in English. A question is a hit@k when a chunk of the expected
document is among the top k results. MRR@5 = mean of 1 / rank of the first hit.

| search | aliases | EN hit@1 | EN MRR@5 | UK hit@1 | UK hit@3 | UK MRR@5 |
|---|---|---:|---:|---:|---:|---:|
| vector | English only | **1.00** | **1.00** | 0.67 | 0.80 | 0.72 |
| hybrid (vector + full-text, RRF) | English only | 0.73 | 0.84 | 0.67 | 0.80 | 0.72 |
| **vector (default)** | **+ Ukrainian** | **1.00** | **1.00** | 0.67 | **0.93** | **0.79** |
| hybrid | + Ukrainian | 0.80 | 0.87 | 0.53 | 0.73 | 0.60 |

- **Vector search is the default.** It finds the right metric first for every English question.
- **Hybrid search did not pay off.** Common domain words ("order", "customer") match 73–80
  of 86 chunks, so the full-text ranking is noise that rank fusion weighs equally with vector
  ranks. RRF and other parameters were deliberately not tuned on a 30-question set.
- **Ukrainian questions are the weak spot** (English-only documents). Ukrainian aliases lift
  the right document into the top 3 more often (hit@3 0.80 → 0.93) but not to rank 1.
- **The alias gain is probably inflated:** aliases and questions were written by the same
  person, and 14 of 15 Ukrainian questions share a word with an alias. To be re-checked on
  independently written questions (milestone 6).

Full reports with every miss: [vector baseline](evals/results/retrieval_baseline.md) ·
[hybrid](evals/results/retrieval_hybrid.md) ·
[Ukrainian aliases](evals/results/retrieval_uk_aliases.md).
Reproduce: `uv run python -m evals.run_evals --label <name>`.

## Answer results

12 `/ask` cases ([cases](evals/answer_cases.json)), each run 3 times per model at effort
`low`: 4 answered (incl. a definition of a metric Olist cannot compute and a numeric
question), 2 ambiguous («ДРР»), 3 no data, 3 off topic (2 near the domain, 1 unrelated,
which the similarity gate rejects without an LLM call). Checks are formal: status, cited
documents, a clarifying question for ambiguous cases, SQL in the numeric answer, answer
language. Prices from claude.com/pricing (USD per 1M tokens, input / output).

| model | price | passed | cost per question | mean latency |
|---|---|---:|---:|---:|
| Claude Opus 5.5 | $4 / $20 | 36/36 | $0.0117 | 4.2 s |
| **Claude Sonnet 5.5 (default)** | $2 / $10 | **36/36** | **$0.0055** | 2.9 s |
| Claude Haiku 5.5 | $0.10 / $0.50 | 32/36 | $0.0003 | 2.3 s |

- **Sonnet 5.5 is the default: the cheapest model that passed every case** in all runs, at
  47% of Opus's cost per question (≈ $5.50 per 1,000 questions vs $11.70). Switch with
  `LLM_MODEL` in `.env`.
- **Haiku 5.5 is ~20x cheaper than Sonnet but failed 4 of 36:** twice it answered an
  English question about «ДРР» in Russian (the docs carry Russian aliases such as «доля
  рекламы»), and twice it left the SQL out of a numeric answer. It also has no server-side
  fallback on refusals.
- **The system prompt is cached:** about 1,400 tokens per call are read from the cache.
- **Caveat:** formal checks only, on cases written by the same person as the docs. Whether
  the answers are *correct* is judged by an LLM on independent questions in milestone 6.

Full report with every answer: [evals/results/answers_models.md](evals/results/answers_models.md).
Reproduce: `uv run python -m evals.run_answer_evals --label models --repeats 3` (≈ $0.60).

## Setup

Requirements: [Docker](https://docs.docker.com/get-docker/) and [uv](https://docs.astral.sh/uv/).
uv installs the pinned Python version (3.11) by itself.

1. **Configure.** Copy `.env.example` to `.env` and set `POSTGRES_PASSWORD`
   (any random string; the database is only reachable from your machine).

2. **Install dependencies.**
   ```bash
   uv sync
   ```

3. **Start Postgres + pgvector.**
   ```bash
   docker compose up -d
   docker compose ps   # wait until STATUS shows "healthy"
   ```

4. **Create the schema.** Safe to re-run: only pending migrations are applied.
   ```bash
   uv run python -m app.migrate
   ```

5. **Download the dataset.** The [Olist Brazilian E-commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
   is public but needs a free Kaggle account. Download the zip and extract the 9 CSV files
   directly into `data/olist/` (git-ignored):
   ```
   data/olist/
     olist_customers_dataset.csv        olist_order_reviews_dataset.csv
     olist_geolocation_dataset.csv      olist_orders_dataset.csv
     olist_order_items_dataset.csv      olist_products_dataset.csv
     olist_order_payments_dataset.csv   olist_sellers_dataset.csv
     product_category_name_translation.csv
   ```

6. **Load the data.** Idempotent: tables are truncated and reloaded in one transaction.
   ```bash
   uv run python -m app.load_olist
   ```

The tables live in the `olist` schema (`olist.orders`, `olist.order_items`, ...).

7. **Index the metric documents.** Needs `OPENAI_API_KEY` in `.env`. Embeds every
   `## ` section of `data/docs/*.md` and stores it in `rag.chunks`. Re-runs are incremental:
   unchanged documents are skipped and only edited sections are sent to the API.
   ```bash
   uv run python -m app.ingest --dry-run   # what would change, no API calls
   uv run python -m app.ingest
   ```

## Ask a question

Start the API (needs `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in `.env`, and the index from
step 7). Interactive docs: http://127.0.0.1:8000/docs.

```bash
uv run python -m uvicorn app.api:app --reload
curl -s -X POST http://127.0.0.1:8000/ask   -H "Content-Type: application/json"   -d '{"question": "How is average order value calculated?"}'
```

The response has the same shape for every question:

| field | meaning |
|---|---|
| `status` | `answered`; `ambiguous` (the term fits several metrics, e.g. «ДРР»: both are explained and `clarifying_question` asks which one); `no_data` (defined, but not computable from Olist); `off_topic` |
| `answer` | the answer, in the language of the question, with `[S1]`-style source markers |
| `sources` | the cited document sections: `doc_id`, `name`, `section` |
| `model`, `usage` | the model that answered, tokens and `cost_usd`; `null` when no LLM was called |

Every answer except `off_topic` cites at least one source, and every cited source is one
the model was actually given; an answer that breaks this is returned as HTTP 502, not shown.
Questions far from any document (best chunk similarity below `OFF_TOPIC_MIN_SIMILARITY`)
are answered without calling the LLM:

```json
{"status": "off_topic",
 "answer": "This question is not covered by the metric documentation, so I cannot answer it.",
 "clarifying_question": null, "sources": [], "model": null, "usage": null}
```

`GET /health` checks the database and returns the number of indexed chunks; it never calls
the paid APIs. Errors: 422 invalid request, 502 unusable upstream answer, 503 a dependency
is down or not configured.

## Metric documents

`data/docs/*.md` define the business metrics the assistant answers about. Each file has
YAML frontmatter (`id`, `name`, `aliases`, `category`, `unit`, `direction`,
`data_availability`, `related`) and fixed `## ` sections (Definition, Formula,
Calculation on Olist data, Interpretation, Pitfalls). `conventions.md` holds the shared
rules (valid order, GMV vs realized revenue, customer identity). `uv run pytest` checks that
every document parses, links resolve and every SQL example runs.

## Development

```bash
uv run ruff check . && uv run ruff format --check .
uv run pytest
```

Tests marked `db` create a throwaway database per test and drop it afterwards; they are
skipped when Postgres is not running.

## Project layout

```
app/          config.py, db.py, migrate.py, load_olist.py, docs.py, embeddings.py, ingest.py,
              retrieval.py, llm.py (Claude client), answer.py (RAG pipeline), api.py (FastAPI)
migrations/   numbered plain-SQL migrations, applied in order
evals/        test set, eval runner, reports (results/)
tests/        unit + integration tests, synthetic Olist fixtures
data/docs/    metric definition documents (indexed for RAG)
data/olist/   Olist CSVs (not committed)
```
