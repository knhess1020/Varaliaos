-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Main memory table
CREATE TABLE IF NOT EXISTS memory (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     text NOT NULL,
    type        text NOT NULL,
    content     text NOT NULL,
    tags        text[] DEFAULT '{}',
    persona     text,
    embedding   vector(1536),
    confidence  float DEFAULT 0,
    merged_into uuid REFERENCES memory(id),
    thread_id   uuid,
    turn        int,
    ts          timestamptz DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_memory_user_id   ON memory (user_id);
CREATE INDEX IF NOT EXISTS idx_memory_type      ON memory (type);
CREATE INDEX IF NOT EXISTS idx_memory_embedding ON memory
    USING hnsw (embedding vector_cosine_ops);
