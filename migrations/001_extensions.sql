-- pgvector: the `vector` column type and similarity operators used for document
-- embeddings from Milestone 2 on. The extension ships with the pgvector Docker image;
-- this statement enables it in our database.
CREATE EXTENSION IF NOT EXISTS vector;
