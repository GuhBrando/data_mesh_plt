#!/usr/bin/env python3
"""Bootstrap a PLATFORM_ADMIN user.

Reads from environment variables or a .env file in the project root.
Safe to re-run: uses upsert so it updates the existing user if the email already exists.

Required env vars:
  PLATFORM_ADMIN_USER  - email address for the admin account
  PLATFORM_ADMIN_PASS  - plaintext password (hashed before storing)

Optional env vars:
  PLATFORM_ADMIN_NAME  - display name (defaults to the part before @)
  MIGRATIONS_DB_HOST   - direct DB host (preferred; falls back to DB_HOST)
"""

import asyncio
import os
import sys
from pathlib import Path

import asyncpg
import bcrypt


def _load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


async def seed() -> None:
    _load_dotenv()

    email = os.environ.get("PLATFORM_ADMIN_USER", "").strip()
    password = os.environ.get("PLATFORM_ADMIN_PASS", "").strip()
    name = os.environ.get("PLATFORM_ADMIN_NAME", "").strip() or email.split("@")[0]

    if not email or not password:
        sys.exit("Error: PLATFORM_ADMIN_USER and PLATFORM_ADMIN_PASS are required")

    db_host = os.environ.get("MIGRATIONS_DB_HOST") or os.environ.get(
        "DB_HOST", "localhost"
    )
    db_port = int(os.environ.get("DB_PORT", "5432"))
    db_user = os.environ.get("DB_USER", "admin")
    db_password = os.environ.get("ADMIN_PASSWORD")
    db_name = os.environ.get("DB_NAME", "data_mesh_plt")
    db_ssl = os.environ.get("DB_SSL_MODE", "require")

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    conn = await asyncpg.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        ssl=db_ssl if db_ssl != "disable" else False,
    )
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO iam.users (name, email, password_hash, role)
            VALUES ($1, $2, $3, 'PLATFORM_ADMIN')
            ON CONFLICT (email) DO UPDATE
                SET name          = EXCLUDED.name,
                    password_hash = EXCLUDED.password_hash,
                    role          = 'PLATFORM_ADMIN'
            RETURNING id, email, role;
            """,
            name,
            email,
            password_hash,
        )
        print(f"Admin ready  →  {row['email']}  (id={row['id']}, role={row['role']})")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(seed())
