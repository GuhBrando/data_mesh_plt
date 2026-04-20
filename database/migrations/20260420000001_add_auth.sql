-- database/migrations/20260420000001_add_auth.sql

ALTER TABLE iam.users ADD COLUMN password_hash TEXT NOT NULL DEFAULT '';
ALTER TABLE iam.users ALTER COLUMN password_hash DROP DEFAULT;

CREATE TABLE iam.refresh_tokens (
    id           UUID PRIMARY KEY,
    user_id      UUID NOT NULL REFERENCES iam.users(id) ON DELETE CASCADE,
    token_hash   TEXT NOT NULL,
    expires_at   TIMESTAMPTZ NOT NULL,
    revoked      BOOLEAN NOT NULL DEFAULT false,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_refresh_tokens_user_id ON iam.refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token_hash ON iam.refresh_tokens(token_hash);
