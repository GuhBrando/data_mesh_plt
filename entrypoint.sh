#!/bin/bash
set -e

if [ -z "$DB_HOST" ]; then
  echo "ERROR: DB_HOST is not set" >&2
  exit 1
fi

echo "Running migrations against $DB_HOST..."
cd /app/database
if atlas migrate apply --env azure; then
  echo "Migrations applied successfully"
else
  echo "WARNING: Migrations failed - check DB_HOST=$DB_HOST is reachable on port 5432"
fi

cd /app
exec uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
