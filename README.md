# analytics-knowledge-assistant

A RAG assistant that answers business questions about e-commerce metrics and data,
exposed as a REST API and as an MCP server, with an evaluation suite.

> Work in progress. Done: database, migrations and Olist data (milestone 1); metric
> documents and their ingestion into pgvector (milestone 2).

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
app/          config.py, db.py, migrate.py, load_olist.py, docs.py, embeddings.py, ingest.py
migrations/   numbered plain-SQL migrations, applied in order
tests/        unit + integration tests, synthetic Olist fixtures
data/docs/    metric definition documents (indexed for RAG)
data/olist/   Olist CSVs (not committed)
```
