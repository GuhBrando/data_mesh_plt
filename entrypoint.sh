#!/bin/bash
set -e

atlas migrate apply \
  --env azure \
  --config /app/database/atlas.hcl

exec uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000
