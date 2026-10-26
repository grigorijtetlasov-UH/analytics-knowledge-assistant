-- RAG storage: metric documents from data/docs/ and their chunks with embeddings.
--
-- * Separate `rag` schema, like `olist`: the read-only SQL tool (Milestone 5) gets access
--   to business data only, not to these tables.
-- * Vector and full-text indexes are added in Milestone 3 (retrieval), where their effect
--   can be measured; with ~100 chunks a sequential scan is instant.

CREATE SCHEMA rag;

CREATE TABLE rag.documents (
    -- Frontmatter `id`, equal to the file name without .md.
    id           text PRIMARY KEY,
    name         text NOT NULL,
    -- The whole frontmatter (aliases, category, unit, data_availability, ...), for filters
    -- and for citing sources in answers.
    metadata     jsonb NOT NULL,
    -- SHA-256 of the file: lets ingestion skip documents that did not change.
    content_hash text NOT NULL,
    updated_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE rag.chunks (
    id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    -- CASCADE: deleting a document removes its chunks in the same statement.
    doc_id          text NOT NULL REFERENCES rag.documents ON DELETE CASCADE,
    -- Position of the chunk in the document (0, 1, ...).
    chunk_index     integer NOT NULL,
    -- The `##` heading the chunk comes from, e.g. "Formula". Shown as the source.
    section         text NOT NULL,
    -- Exactly the text that was embedded (with the metric name/section header).
    content         text NOT NULL,
    -- SHA-256 of `content`: ingestion reuses an existing embedding for identical text
    -- instead of calling the embeddings API again.
    content_hash    text NOT NULL,
    -- 1536 = output size of OpenAI text-embedding-3-small. A model with another size
    -- needs a new migration that changes this column.
    embedding       vector(1536) NOT NULL,
    -- Embeddings from different models are not comparable; the model is stored per chunk
    -- so a model switch re-embeds everything instead of mixing vectors.
    embedding_model text NOT NULL,
    UNIQUE (doc_id, chunk_index)
);
CREATE INDEX ON rag.chunks (content_hash, embedding_model);
