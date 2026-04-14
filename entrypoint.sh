#!/bin/bash
set -e

if [ -z "$DB_HOST" ]; then
  echo "ERROR: DB_HOST is not set" >&2
  exit 1
fi

ATLAS_HOST="${MIGRATIONS_DB_HOST:-$DB_HOST}"
ATLAS_URL="postgres://${DB_USER}:${ADMIN_PASSWORD}@${ATLAS_HOST}:${DB_PORT}/${DB_NAME}?sslmode=require"

echo "Running migrations against $ATLAS_HOST..."
cd /app/database
if atlas migrate apply --env azure --url "$ATLAS_URL" --revisions-schema public; then
  echo "Migrations applied successfully"
else
  echo "WARNING: Migrations failed - check $ATLAS_HOST is reachable on port $DB_PORT"
fi

cd /app
exec uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
