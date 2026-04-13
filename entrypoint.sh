#!/bin/bash
set -e

if [ -z "$DB_HOST" ]; then
  echo "ERROR: DB_HOST is not set" >&2
  exit 1
fi

echo "Running migrations against $DB_HOST..."
cd /app/database
atlas migrate apply --env azure

cd /app
exec uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
