-- Audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id       bigserial PRIMARY KEY,
    user_id  text NOT NULL,
    action   text NOT NULL,
    mem_id   uuid,
    ts       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_log (user_id);
