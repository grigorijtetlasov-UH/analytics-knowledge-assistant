-- Full-text search column and search indexes for rag.chunks (Milestone 3).

-- `tsv` is computed by Postgres from `content` and kept in sync automatically
-- (GENERATED ... STORED), so ingestion does not have to fill it. Two parts:
-- * The chunk header (first line: "Name (id; also: aliases) — Section") with the
--   `simple` config: lowercased, no stemming, no stop words. Abbreviations and aliases in any
--   language ("ДРР", "LTV", "OTD") stay exact tokens. Weight A: a header match ranks highest.
-- * The whole chunk with the `english` config: English stemming ("orders" matches
--   "order") and English stop words removed. Weight B.
-- Postgres has no built-in Ukrainian dictionary, so Ukrainian words only match exactly
-- (via `simple` in the header, or unchanged by the English stemmer in the body).
ALTER TABLE rag.chunks ADD COLUMN tsv tsvector GENERATED ALWAYS AS (
    setweight(to_tsvector('simple', split_part(content, E'\n', 1)), 'A')
    || setweight(to_tsvector('english', content), 'B')
) STORED;

-- With ~100 chunks neither index makes queries faster: the planner scans the table anyway.
-- They are here so search stays fast when the number of documents grows.
CREATE INDEX ON rag.chunks USING gin (tsv);
-- HNSW: approximate nearest-neighbour index for cosine distance (the <=> operator).
CREATE INDEX ON rag.chunks USING hnsw (embedding vector_cosine_ops);
