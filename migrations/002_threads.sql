-- Conversation thread table
CREATE TABLE IF NOT EXISTS conversation_thread (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     text NOT NULL,
    persona     text NOT NULL,
    started_at  timestamptz NOT NULL DEFAULT now(),
    last_turn   int NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_thread_user_persona
    ON conversation_thread (user_id, persona);
