-- database/migrations/20260420000001_add_auth.sql

ALTER TABLE iam.users ADD COLUMN password_hash TEXT NOT NULL DEFAULT '';
ALTER TABLE iam.users ALTER COLUMN password_hash DROP DEFAULT;

CREATE TABLE iam.refresh_tokens (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES iam.users(id) ON DELETE CASCADE,
    token_hash   TEXT NOT NULL,
    expires_at   TIMESTAMPTZ NOT NULL,
    revoked      BOOLEAN NOT NULL DEFAULT false,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_refresh_tokens_user_id ON iam.refresh_tokens(user_id);
CREATE UNIQUE INDEX idx_refresh_tokens_token_hash ON iam.refresh_tokens(token_hash);

GRANT SELECT, INSERT, UPDATE, DELETE ON iam.refresh_tokens TO app_user;

-- Rollback:
-- DROP TABLE iam.refresh_tokens;
-- ALTER TABLE iam.users DROP COLUMN password_hash;
-- REVOKE SELECT, INSERT, UPDATE, DELETE ON iam.refresh_tokens FROM app_user;
