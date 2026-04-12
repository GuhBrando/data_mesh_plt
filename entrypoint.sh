#!/bin/bash
set -e

cd /app/database
atlas migrate apply --env azure

cd /app
exec uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
