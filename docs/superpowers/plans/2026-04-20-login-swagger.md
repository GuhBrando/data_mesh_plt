# Login via Swagger Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add JWT Bearer token authentication to the FastAPI backend, protecting all existing endpoints and exposing login/refresh/logout via the Swagger UI Authorize button.

**Architecture:** Clean hexagonal architecture — new `use_cases/auth/` module, `RefreshToken` domain entity, `PostgresRefreshTokenRepository`, and `interface/security.py` for JWT helpers and the `get_current_user` FastAPI dependency. Access tokens (15 min) are stateless JWTs; refresh tokens (7 days) are stored as SHA-256 hashes in `iam.refresh_tokens` using the JWT's `jti` claim as the primary key for O(1) lookup.

**Tech Stack:** FastAPI, asyncpg (raw SQL), PyJWT 2.12.1, bcrypt 5.0.0, pytest, pytest-asyncio, httpx

---

## File Map

**Create:**
- `database/migrations/20260420000001_add_auth.sql` — adds `password_hash` to `iam.users`, creates `iam.refresh_tokens`
- `backend/domain/entities/refresh_token.py` — `RefreshToken` entity
- `backend/domain/interfaces/refresh_token_repository.py` — `IRefreshTokenRepository` ABC
- `backend/infra/repositories/refresh_token_repository.py` — `PostgresRefreshTokenRepository`
- `backend/use_cases/auth/__init__.py` — empty
- `backend/use_cases/auth/login.py` — `LoginUseCase`
- `backend/use_cases/auth/refresh.py` — `RefreshUseCase`
- `backend/use_cases/auth/logout.py` — `LogoutUseCase`
- `backend/interface/security.py` — JWT helpers + `get_current_user` dependency
- `backend/interface/schemas/auth.py` — `LoginRequest`, `LoginResponse`, `TokenResponse`, `RefreshRequest`, `LogoutRequest`
- `backend/interface/routers/auth.py` — `/auth/login`, `/auth/refresh`, `/auth/logout`
- `tests/unit/__init__.py`
- `tests/unit/interface/__init__.py`
- `tests/unit/interface/test_security.py`
- `tests/unit/use_cases/__init__.py`
- `tests/unit/use_cases/auth/__init__.py`
- `tests/unit/use_cases/auth/test_login.py`
- `tests/unit/use_cases/auth/test_refresh.py`
- `tests/unit/use_cases/auth/test_logout.py`
- `tests/unit/interface/test_password_policy.py`

**Modify:**
- `pyproject.toml` — add `PyJWT`, `bcrypt`; add `pytest-asyncio`, `httpx` to dev deps
- `backend/infra/config.py` — add `JWT_SECRET_KEY`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, `JWT_REFRESH_TOKEN_EXPIRE_DAYS`
- `backend/domain/entities/user.py` — add `password_hash: str` field
- `backend/domain/interfaces/user_repository.py` — add `get_by_email` abstract method; update `create` signature
- `backend/infra/repositories/user_repository.py` — update `create` to accept `password_hash`; add `get_by_email`
- `backend/interface/schemas/user.py` — make `password` required; add Pydantic policy validator
- `backend/use_cases/user/create.py` — accept `password`, hash it, pass hash to repo
- `backend/interface/routers/users.py` — pass `body.password` to use case; add `get_current_user` dep to all routes
- `backend/interface/routers/data_contract.py` — add `get_current_user` dep to all routes
- `backend/interface/routers/data_product.py` — add `get_current_user` dep to all routes
- `backend/interface/dependencies.py` — add auth repo + use case factory functions
- `backend/interface/routers/__init__.py` — include auth router

---

## Task 1: DB Migration

**Files:**
- Create: `database/migrations/20260420000001_add_auth.sql`

- [ ] **Step 1: Create the migration file**

```sql
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
```

- [ ] **Step 2: Apply the migration via Atlas**

```bash
# From the project root — adjust env vars to match your local .env
atlas migrate apply \
  --dir "file://database/migrations" \
  --url "postgres://admin:${ADMIN_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?sslmode=require"
```

Expected output: `Migrating to version 20260420000001 (1 migration in total)`

- [ ] **Step 3: Commit**

```bash
git add database/migrations/20260420000001_add_auth.sql
git commit -m "feat: add password_hash to users and refresh_tokens table"
```

---

## Task 2: Install Dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Update `pyproject.toml`**

In `[project] dependencies`, add:
```toml
dependencies = [
    "setuptools==80.9.0",
    "wheel==0.45.1",
    "uvicorn[standard]>=0.23.0",
    "fastapi==0.128.0",
    "asyncpg==0.31.0",
    "python-dotenv>=1.0.0",
    "PyJWT>=2.12.1",
    "bcrypt>=5.0.0",
]
```

In `[project.optional-dependencies] dev`, add:
```toml
dev = [
    "ruff",
    "pre-commit>=3.4.0",
    "pip-tools>=6.15.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "httpx>=0.27.0",
]
```

Add a new section for pytest config (so `@pytest.mark.asyncio` works without extra decoration):
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 2: Install**

```bash
pip install PyJWT>=2.12.1 bcrypt>=5.0.0 pytest-asyncio>=0.23.0 httpx>=0.27.0
```

Expected: packages install without errors.

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "feat: add PyJWT, bcrypt, pytest-asyncio, httpx dependencies"
```

---

## Task 3: Update Config

**Files:**
- Modify: `backend/infra/config.py`

- [ ] **Step 1: Add JWT config vars**

Replace the full content of `backend/infra/config.py`:

```python
import os

from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("ADMIN_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "data_mesh_plt")

_raw_cors = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
CORS_ORIGINS = [o.strip() for o in _raw_cors.split(",") if o.strip()]

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
JWT_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
```

- [ ] **Step 2: Add JWT vars to `.env`**

Add to your `.env` file (never commit this file):
```
JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

- [ ] **Step 3: Commit**

```bash
git add backend/infra/config.py
git commit -m "feat: add JWT config vars to config"
```

---

## Task 4: Update User Entity

**Files:**
- Modify: `backend/domain/entities/user.py`

- [ ] **Step 1: Add `password_hash` field**

```python
import uuid

from backend.domain.value_objects.email import Email


class User:
    def __init__(self, id: uuid.UUID, name: str, email: Email, password_hash: str = ""):
        self.id = id
        self.name = name
        self.email = email
        self.password_hash = password_hash

    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, email={self.email})"
```

- [ ] **Step 2: Commit**

```bash
git add backend/domain/entities/user.py
git commit -m "feat: add password_hash field to User entity"
```

---

## Task 5: Update User Repository Interface and Implementation

**Files:**
- Modify: `backend/domain/interfaces/user_repository.py`
- Modify: `backend/infra/repositories/user_repository.py`

- [ ] **Step 1: Update the interface**

```python
import uuid
from abc import ABC, abstractmethod

from backend.domain.entities.user import User


class IUserRepository(ABC):
    @abstractmethod
    async def create(self, name: str, email: str, password_hash: str) -> User: ...

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> User | None: ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    async def list(self) -> list[User]: ...

    @abstractmethod
    async def update(
        self, user_id: uuid.UUID, name: str | None, email: str | None
    ) -> User | None: ...

    @abstractmethod
    async def delete(self, user_id: uuid.UUID) -> bool: ...
```

- [ ] **Step 2: Update the implementation**

```python
import uuid

from backend.domain.entities.user import User
from backend.domain.interfaces.user_repository import IUserRepository
from backend.domain.value_objects.email import Email


class PostgresUserRepository(IUserRepository):
    def __init__(self, db):
        self.db = db

    async def create(self, name: str, email: str, password_hash: str) -> User:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                INSERT INTO iam.users (name, email, password_hash)
                VALUES ($1, $2, $3)
                RETURNING id, name, email, password_hash;
                """,
                name,
                email,
                password_hash,
            )
            return User(
                id=row["id"],
                name=row["name"],
                email=Email(row["email"]),
                password_hash=row["password_hash"],
            )

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        row = await self.db.fetchrow(
            "SELECT id, name, email, password_hash FROM iam.users WHERE id = $1;",
            user_id,
        )
        if row:
            return User(
                id=row["id"],
                name=row["name"],
                email=Email(row["email"]),
                password_hash=row["password_hash"],
            )
        return None

    async def get_by_email(self, email: str) -> User | None:
        row = await self.db.fetchrow(
            "SELECT id, name, email, password_hash FROM iam.users WHERE email = $1;",
            email,
        )
        if row:
            return User(
                id=row["id"],
                name=row["name"],
                email=Email(row["email"]),
                password_hash=row["password_hash"],
            )
        return None

    async def list(self) -> list[User]:
        rows = await self.db.fetch(
            "SELECT id, name, email, password_hash FROM iam.users;"
        )
        return [
            User(
                id=r["id"],
                name=r["name"],
                email=Email(r["email"]),
                password_hash=r["password_hash"],
            )
            for r in rows
        ]

    async def update(
        self, user_id: uuid.UUID, name: str | None, email: str | None
    ) -> User | None:
        updates: dict = {}
        if name is not None:
            updates["name"] = name
        if email is not None:
            updates["email"] = email

        if not updates:
            return await self.get_by_id(user_id)

        set_clauses = ", ".join(f"{col} = ${i + 1}" for i, col in enumerate(updates))
        values = list(updates.values()) + [user_id]

        async with self.db.transaction():
            row = await self.db.fetchrow(
                f"""
                UPDATE iam.users
                SET {set_clauses}
                WHERE id = ${len(values)}
                RETURNING id, name, email, password_hash;
                """,
                *values,
            )
            if row:
                return User(
                    id=row["id"],
                    name=row["name"],
                    email=Email(row["email"]),
                    password_hash=row["password_hash"],
                )
            return None

    async def delete(self, user_id: uuid.UUID) -> bool:
        async with self.db.transaction():
            result = await self.db.execute(
                "DELETE FROM iam.users WHERE id = $1;",
                user_id,
            )
            return result == "DELETE 1"
```

- [ ] **Step 3: Commit**

```bash
git add backend/domain/interfaces/user_repository.py backend/infra/repositories/user_repository.py
git commit -m "feat: add get_by_email and password_hash to user repository"
```

---

## Task 6: RefreshToken Entity and Interface

**Files:**
- Create: `backend/domain/entities/refresh_token.py`
- Create: `backend/domain/interfaces/refresh_token_repository.py`

- [ ] **Step 1: Create RefreshToken entity**

```python
# backend/domain/entities/refresh_token.py
import uuid
from datetime import datetime


class RefreshToken:
    def __init__(
        self,
        id: uuid.UUID,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        revoked: bool,
    ):
        self.id = id
        self.user_id = user_id
        self.token_hash = token_hash
        self.expires_at = expires_at
        self.revoked = revoked
```

- [ ] **Step 2: Create IRefreshTokenRepository interface**

```python
# backend/domain/interfaces/refresh_token_repository.py
import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from backend.domain.entities.refresh_token import RefreshToken


class IRefreshTokenRepository(ABC):
    @abstractmethod
    async def create(
        self,
        id: uuid.UUID,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken: ...

    @abstractmethod
    async def get_by_id(self, token_id: uuid.UUID) -> RefreshToken | None: ...

    @abstractmethod
    async def revoke(self, token_id: uuid.UUID) -> None: ...
```

- [ ] **Step 3: Commit**

```bash
git add backend/domain/entities/refresh_token.py backend/domain/interfaces/refresh_token_repository.py
git commit -m "feat: add RefreshToken entity and IRefreshTokenRepository"
```

---

## Task 7: PostgresRefreshTokenRepository

**Files:**
- Create: `backend/infra/repositories/refresh_token_repository.py`

- [ ] **Step 1: Create the implementation**

```python
# backend/infra/repositories/refresh_token_repository.py
import uuid
from datetime import datetime

from backend.domain.entities.refresh_token import RefreshToken
from backend.domain.interfaces.refresh_token_repository import IRefreshTokenRepository


class PostgresRefreshTokenRepository(IRefreshTokenRepository):
    def __init__(self, db):
        self.db = db

    async def create(
        self,
        id: uuid.UUID,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        async with self.db.transaction():
            row = await self.db.fetchrow(
                """
                INSERT INTO iam.refresh_tokens (id, user_id, token_hash, expires_at)
                VALUES ($1, $2, $3, $4)
                RETURNING id, user_id, token_hash, expires_at, revoked;
                """,
                id,
                user_id,
                token_hash,
                expires_at,
            )
            return RefreshToken(
                id=row["id"],
                user_id=row["user_id"],
                token_hash=row["token_hash"],
                expires_at=row["expires_at"],
                revoked=row["revoked"],
            )

    async def get_by_id(self, token_id: uuid.UUID) -> RefreshToken | None:
        row = await self.db.fetchrow(
            """
            SELECT id, user_id, token_hash, expires_at, revoked
            FROM iam.refresh_tokens
            WHERE id = $1;
            """,
            token_id,
        )
        if row:
            return RefreshToken(
                id=row["id"],
                user_id=row["user_id"],
                token_hash=row["token_hash"],
                expires_at=row["expires_at"],
                revoked=row["revoked"],
            )
        return None

    async def revoke(self, token_id: uuid.UUID) -> None:
        await self.db.execute(
            "UPDATE iam.refresh_tokens SET revoked = true WHERE id = $1;",
            token_id,
        )
```

- [ ] **Step 2: Commit**

```bash
git add backend/infra/repositories/refresh_token_repository.py
git commit -m "feat: add PostgresRefreshTokenRepository"
```

---

## Task 8: JWT Security Module

**Files:**
- Create: `backend/interface/security.py`
- Create: `tests/unit/interface/__init__.py`
- Create: `tests/unit/__init__.py`
- Create: `tests/unit/interface/test_security.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/__init__.py
# (empty)

# tests/unit/interface/__init__.py
# (empty)
```

```python
# tests/unit/interface/test_security.py
import time
import uuid

import pytest

from backend.interface.security import create_access_token, decode_token


def test_create_access_token_returns_string():
    token = create_access_token(user_id="test-user-id", secret_key="testsecret", expire_minutes=15)
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_token_returns_correct_sub():
    token = create_access_token(user_id="user-123", secret_key="testsecret", expire_minutes=15)
    payload = decode_token(token, secret_key="testsecret")
    assert payload["sub"] == "user-123"


def test_decode_token_raises_on_expired():
    from fastapi import HTTPException
    token = create_access_token(user_id="user-123", secret_key="testsecret", expire_minutes=-1)
    with pytest.raises(HTTPException) as exc:
        decode_token(token, secret_key="testsecret")
    assert exc.value.status_code == 401
    assert "expired" in exc.value.detail.lower()


def test_decode_token_raises_on_invalid():
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        decode_token("not.a.valid.token", secret_key="testsecret")
    assert exc.value.status_code == 401


def test_create_refresh_token_contains_jti():
    jti = str(uuid.uuid4())
    token = create_refresh_token(
        jti=jti, user_id="user-123", secret_key="testsecret", expire_days=7
    )
    payload = decode_token(token, secret_key="testsecret")
    assert payload["jti"] == jti
    assert payload["sub"] == "user-123"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/unit/interface/test_security.py -v
```

Expected: `ImportError` or `ModuleNotFoundError` — `security.py` does not exist yet.

- [ ] **Step 3: Create `backend/interface/security.py`**

```python
# backend/interface/security.py
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.infra.config import (
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    JWT_SECRET_KEY,
)
from backend.infra.postgres import get_db_connection

ALGORITHM = "HS256"
bearer_scheme = HTTPBearer()


def create_access_token(
    user_id: str,
    secret_key: str = JWT_SECRET_KEY,
    expire_minutes: int = JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    return jwt.encode({"sub": user_id, "exp": expire}, secret_key, algorithm=ALGORITHM)


def create_refresh_token(
    jti: str,
    user_id: str,
    secret_key: str = JWT_SECRET_KEY,
    expire_days: int = JWT_REFRESH_TOKEN_EXPIRE_DAYS,
) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=expire_days)
    return jwt.encode(
        {"sub": user_id, "jti": jti, "exp": expire}, secret_key, algorithm=ALGORITHM
    )


def decode_token(token: str, secret_key: str = JWT_SECRET_KEY) -> dict:
    try:
        return jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db=Depends(get_db_connection),
):
    from backend.infra.repositories.user_repository import PostgresUserRepository

    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    repo = PostgresUserRepository(db)
    user = await repo.get_by_id(uuid.UUID(user_id))
    if not user:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return user
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/interface/test_security.py -v
```

Expected: all 5 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/interface/security.py tests/unit/__init__.py tests/unit/interface/__init__.py tests/unit/interface/test_security.py
git commit -m "feat: add JWT security module with create/decode helpers and get_current_user"
```

---

## Task 9: Password Policy Validator

**Files:**
- Modify: `backend/interface/schemas/user.py`
- Create: `tests/unit/interface/test_password_policy.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/interface/test_password_policy.py
import pytest
from pydantic import ValidationError

from backend.interface.schemas.user import UserCreateModel


def test_valid_password_passes():
    m = UserCreateModel(username="Alice", email="a@b.com", password="Str0ng!Pass")
    assert m.password == "Str0ng!Pass"


def test_password_too_short_raises():
    with pytest.raises(ValidationError, match="8 characters"):
        UserCreateModel(username="Alice", email="a@b.com", password="Ab1!")


def test_password_no_uppercase_raises():
    with pytest.raises(ValidationError, match="uppercase"):
        UserCreateModel(username="Alice", email="a@b.com", password="str0ng!pass")


def test_password_no_lowercase_raises():
    with pytest.raises(ValidationError, match="lowercase"):
        UserCreateModel(username="Alice", email="a@b.com", password="STR0NG!PASS")


def test_password_no_digit_raises():
    with pytest.raises(ValidationError, match="number"):
        UserCreateModel(username="Alice", email="a@b.com", password="Strong!Pass")


def test_password_no_special_raises():
    with pytest.raises(ValidationError, match="special character"):
        UserCreateModel(username="Alice", email="a@b.com", password="Str0ngPass1")


def test_password_required():
    with pytest.raises(ValidationError):
        UserCreateModel(username="Alice", email="a@b.com")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/unit/interface/test_password_policy.py -v
```

Expected: failures because `password` is currently `Optional[str] = None` with no validator.

- [ ] **Step 3: Update `backend/interface/schemas/user.py`**

```python
import re
import uuid

from pydantic import BaseModel, field_validator


class UserCreateModel(BaseModel):
    username: str
    email: str
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError(
                "Password must contain at least one special character (!@#$%^&*)"
            )
        return v


class UserResponseModel(BaseModel):
    id: uuid.UUID
    username: str
    email: str


class UserUpdateModel(BaseModel):
    username: str | None = None
    email: str | None = None


class UserIdentity(BaseModel):
    id: uuid.UUID
    name: str
    email: str
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/interface/test_password_policy.py -v
```

Expected: all 7 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/interface/schemas/user.py tests/unit/interface/test_password_policy.py
git commit -m "feat: add password policy validator to UserCreateModel"
```

---

## Task 10: Update CreateUserUseCase to Hash Password

**Files:**
- Modify: `backend/use_cases/user/create.py`
- Modify: `backend/interface/routers/users.py`

- [ ] **Step 1: Update `CreateUserUseCase`**

```python
# backend/use_cases/user/create.py
import bcrypt

from backend.domain.entities.user import User
from backend.domain.interfaces.user_repository import IUserRepository
from backend.domain.value_objects.email import Email


class CreateUserUseCase:
    def __init__(self, repository: IUserRepository):
        self.repository = repository

    async def execute(self, name: str, email: str, password: str) -> User:
        Email(email)  # raises ValueError if invalid
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        return await self.repository.create(name=name, email=email, password_hash=password_hash)
```

- [ ] **Step 2: Update `create_user` route in `backend/interface/routers/users.py`**

Find the `create_user` endpoint and update the `use_case.execute` call:

```python
@router.post("/users", response_model=UserResponseModel, status_code=201)
async def create_user(
    body: UserCreateModel,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
):
    try:
        user = await use_case.execute(name=body.username, email=body.email, password=body.password)
        return _to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

- [ ] **Step 3: Run existing tests**

```bash
pytest tests/ -v
```

Expected: existing `test_main.py` still passes.

- [ ] **Step 4: Commit**

```bash
git add backend/use_cases/user/create.py backend/interface/routers/users.py
git commit -m "feat: hash password in CreateUserUseCase"
```

---

## Task 11: LoginUseCase

**Files:**
- Create: `backend/use_cases/auth/__init__.py`
- Create: `backend/use_cases/auth/login.py`
- Create: `tests/unit/use_cases/__init__.py`
- Create: `tests/unit/use_cases/auth/__init__.py`
- Create: `tests/unit/use_cases/auth/test_login.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/use_cases/__init__.py
# (empty)

# tests/unit/use_cases/auth/__init__.py
# (empty)
```

```python
# tests/unit/use_cases/auth/test_login.py
import hashlib
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import bcrypt
import pytest
from fastapi import HTTPException

from backend.domain.entities.refresh_token import RefreshToken
from backend.domain.entities.user import User
from backend.domain.value_objects.email import Email
from backend.use_cases.auth.login import LoginUseCase


def _make_user(password: str) -> User:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return User(
        id=uuid.uuid4(),
        name="Alice",
        email=Email("alice@example.com"),
        password_hash=hashed,
    )


def _make_token_repo() -> AsyncMock:
    repo = AsyncMock()
    repo.create.return_value = RefreshToken(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        token_hash="hash",
        expires_at=datetime.now(timezone.utc),
        revoked=False,
    )
    return repo


@pytest.mark.asyncio
async def test_login_returns_tokens_on_valid_credentials():
    user = _make_user("Str0ng!Pass")
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = user
    token_repo = _make_token_repo()

    use_case = LoginUseCase(user_repo=user_repo, token_repo=token_repo)
    result = await use_case.execute(email="alice@example.com", password="Str0ng!Pass")

    assert "access_token" in result
    assert "refresh_token" in result
    assert result["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_raises_401_on_wrong_password():
    user = _make_user("Str0ng!Pass")
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = user
    token_repo = _make_token_repo()

    use_case = LoginUseCase(user_repo=user_repo, token_repo=token_repo)
    with pytest.raises(HTTPException) as exc:
        await use_case.execute(email="alice@example.com", password="WrongPass1!")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_raises_401_on_unknown_email():
    user_repo = AsyncMock()
    user_repo.get_by_email.return_value = None
    token_repo = _make_token_repo()

    use_case = LoginUseCase(user_repo=user_repo, token_repo=token_repo)
    with pytest.raises(HTTPException) as exc:
        await use_case.execute(email="nobody@example.com", password="Str0ng!Pass")
    assert exc.value.status_code == 401
    assert exc.value.detail == "Invalid credentials"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/unit/use_cases/auth/test_login.py -v
```

Expected: `ImportError` — `LoginUseCase` does not exist yet.

- [ ] **Step 3: Create `backend/use_cases/auth/__init__.py` (empty) and `login.py`**

```python
# backend/use_cases/auth/__init__.py
# (empty)
```

```python
# backend/use_cases/auth/login.py
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException

from backend.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from backend.domain.interfaces.user_repository import IUserRepository
from backend.infra.config import JWT_REFRESH_TOKEN_EXPIRE_DAYS
from backend.interface.security import create_access_token, create_refresh_token


class LoginUseCase:
    def __init__(
        self,
        user_repo: IUserRepository,
        token_repo: IRefreshTokenRepository,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def execute(self, email: str, password: str) -> dict:
        user = await self.user_repo.get_by_email(email)
        if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        jti = str(uuid.uuid4())
        access_token = create_access_token(user_id=str(user.id))
        refresh_token = create_refresh_token(jti=jti, user_id=str(user.id))

        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        expires_at = datetime.now(timezone.utc) + timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        await self.token_repo.create(
            id=uuid.UUID(jti),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/use_cases/auth/test_login.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/use_cases/auth/__init__.py backend/use_cases/auth/login.py tests/unit/use_cases/__init__.py tests/unit/use_cases/auth/__init__.py tests/unit/use_cases/auth/test_login.py
git commit -m "feat: add LoginUseCase with bcrypt verification and token issuance"
```

---

## Task 12: RefreshUseCase

**Files:**
- Create: `backend/use_cases/auth/refresh.py`
- Create: `tests/unit/use_cases/auth/test_refresh.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/use_cases/auth/test_refresh.py
import hashlib
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from backend.domain.entities.refresh_token import RefreshToken
from backend.interface.security import create_refresh_token
from backend.use_cases.auth.refresh import RefreshUseCase

SECRET = "testsecret"


def _make_stored_token(raw_token: str, revoked: bool = False) -> RefreshToken:
    return RefreshToken(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc),
        revoked=revoked,
    )


@pytest.mark.asyncio
async def test_refresh_returns_new_access_token():
    jti = str(uuid.uuid4())
    raw_token = create_refresh_token(jti=jti, user_id="user-1", secret_key=SECRET, expire_days=7)
    stored = _make_stored_token(raw_token)
    stored.id = uuid.UUID(jti)

    token_repo = AsyncMock()
    token_repo.get_by_id.return_value = stored

    use_case = RefreshUseCase(token_repo=token_repo, secret_key=SECRET)
    result = await use_case.execute(refresh_token=raw_token)

    assert "access_token" in result
    assert result["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_raises_401_on_revoked_token():
    jti = str(uuid.uuid4())
    raw_token = create_refresh_token(jti=jti, user_id="user-1", secret_key=SECRET, expire_days=7)
    stored = _make_stored_token(raw_token, revoked=True)
    stored.id = uuid.UUID(jti)

    token_repo = AsyncMock()
    token_repo.get_by_id.return_value = stored

    use_case = RefreshUseCase(token_repo=token_repo, secret_key=SECRET)
    with pytest.raises(HTTPException) as exc:
        await use_case.execute(refresh_token=raw_token)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_raises_401_on_tampered_token():
    jti = str(uuid.uuid4())
    raw_token = create_refresh_token(jti=jti, user_id="user-1", secret_key=SECRET, expire_days=7)
    stored = _make_stored_token("different_token_altogether")
    stored.id = uuid.UUID(jti)

    token_repo = AsyncMock()
    token_repo.get_by_id.return_value = stored

    use_case = RefreshUseCase(token_repo=token_repo, secret_key=SECRET)
    with pytest.raises(HTTPException) as exc:
        await use_case.execute(refresh_token=raw_token)
    assert exc.value.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/unit/use_cases/auth/test_refresh.py -v
```

Expected: `ImportError` — `RefreshUseCase` does not exist yet.

- [ ] **Step 3: Create `backend/use_cases/auth/refresh.py`**

```python
# backend/use_cases/auth/refresh.py
import hashlib
import uuid

from fastapi import HTTPException

from backend.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from backend.infra.config import JWT_SECRET_KEY
from backend.interface.security import create_access_token, decode_token


class RefreshUseCase:
    def __init__(
        self,
        token_repo: IRefreshTokenRepository,
        secret_key: str = JWT_SECRET_KEY,
    ):
        self.token_repo = token_repo
        self.secret_key = secret_key

    async def execute(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token, secret_key=self.secret_key)
        jti = payload.get("jti")
        user_id = payload.get("sub")
        if not jti or not user_id:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        stored = await self.token_repo.get_by_id(uuid.UUID(jti))
        token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
        if not stored or stored.revoked or stored.token_hash != token_hash:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        access_token = create_access_token(user_id=user_id, secret_key=self.secret_key)
        return {"access_token": access_token, "token_type": "bearer"}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/use_cases/auth/test_refresh.py -v
```

Expected: all 3 tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/use_cases/auth/refresh.py tests/unit/use_cases/auth/test_refresh.py
git commit -m "feat: add RefreshUseCase with SHA-256 token hash verification"
```

---

## Task 13: LogoutUseCase

**Files:**
- Create: `backend/use_cases/auth/logout.py`
- Create: `tests/unit/use_cases/auth/test_logout.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/unit/use_cases/auth/test_logout.py
import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException

from backend.interface.security import create_refresh_token
from backend.use_cases.auth.logout import LogoutUseCase

SECRET = "testsecret"


@pytest.mark.asyncio
async def test_logout_revokes_token():
    jti = str(uuid.uuid4())
    raw_token = create_refresh_token(jti=jti, user_id="user-1", secret_key=SECRET, expire_days=7)

    token_repo = AsyncMock()
    use_case = LogoutUseCase(token_repo=token_repo, secret_key=SECRET)
    await use_case.execute(refresh_token=raw_token)

    token_repo.revoke.assert_awaited_once_with(uuid.UUID(jti))


@pytest.mark.asyncio
async def test_logout_raises_401_on_invalid_token():
    token_repo = AsyncMock()
    use_case = LogoutUseCase(token_repo=token_repo, secret_key=SECRET)

    with pytest.raises(HTTPException) as exc:
        await use_case.execute(refresh_token="not.a.valid.token")
    assert exc.value.status_code == 401
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/unit/use_cases/auth/test_logout.py -v
```

Expected: `ImportError` — `LogoutUseCase` does not exist yet.

- [ ] **Step 3: Create `backend/use_cases/auth/logout.py`**

```python
# backend/use_cases/auth/logout.py
import uuid

from fastapi import HTTPException

from backend.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from backend.infra.config import JWT_SECRET_KEY
from backend.interface.security import decode_token


class LogoutUseCase:
    def __init__(
        self,
        token_repo: IRefreshTokenRepository,
        secret_key: str = JWT_SECRET_KEY,
    ):
        self.token_repo = token_repo
        self.secret_key = secret_key

    async def execute(self, refresh_token: str) -> None:
        payload = decode_token(refresh_token, secret_key=self.secret_key)
        jti = payload.get("jti")
        if not jti:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        await self.token_repo.revoke(uuid.UUID(jti))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/unit/use_cases/auth/test_logout.py -v
```

Expected: all 2 tests pass.

- [ ] **Step 5: Run all unit tests**

```bash
pytest tests/unit/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/use_cases/auth/logout.py tests/unit/use_cases/auth/test_logout.py
git commit -m "feat: add LogoutUseCase with jti-based token revocation"
```

---

## Task 14: Auth Schemas and Router

**Files:**
- Create: `backend/interface/schemas/auth.py`
- Create: `backend/interface/routers/auth.py`

- [ ] **Step 1: Create auth schemas**

```python
# backend/interface/schemas/auth.py
from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
```

- [ ] **Step 2: Create auth router**

```python
# backend/interface/routers/auth.py
from fastapi import APIRouter, Depends

from backend.domain.entities.user import User
from backend.interface.dependencies import (
    get_login_use_case,
    get_logout_use_case,
    get_refresh_use_case,
)
from backend.interface.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
)
from backend.interface.security import get_current_user
from backend.use_cases.auth.login import LoginUseCase
from backend.use_cases.auth.logout import LogoutUseCase
from backend.use_cases.auth.refresh import RefreshUseCase

router = APIRouter()


@router.post("/auth/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    use_case: LoginUseCase = Depends(get_login_use_case),
):
    return await use_case.execute(email=body.email, password=body.password)


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    use_case: RefreshUseCase = Depends(get_refresh_use_case),
):
    return await use_case.execute(refresh_token=body.refresh_token)


@router.post("/auth/logout", status_code=200)
async def logout(
    body: LogoutRequest,
    use_case: LogoutUseCase = Depends(get_logout_use_case),
    _: User = Depends(get_current_user),
):
    await use_case.execute(refresh_token=body.refresh_token)
    return {"detail": "Successfully logged out"}
```

- [ ] **Step 3: Commit**

```bash
git add backend/interface/schemas/auth.py backend/interface/routers/auth.py
git commit -m "feat: add auth schemas and router"
```

---

## Task 15: Wire Auth into Dependencies and Routers

**Files:**
- Modify: `backend/interface/dependencies.py`
- Modify: `backend/interface/routers/__init__.py`

- [ ] **Step 1: Add auth factory functions to `dependencies.py`**

Add these imports at the top of `backend/interface/dependencies.py`:

```python
from backend.infra.repositories.refresh_token_repository import PostgresRefreshTokenRepository
from backend.use_cases.auth.login import LoginUseCase
from backend.use_cases.auth.refresh import RefreshUseCase
from backend.use_cases.auth.logout import LogoutUseCase
```

Add these functions at the bottom of `backend/interface/dependencies.py`:

```python
# --- Auth ---

def get_refresh_token_repository(
    db=Depends(get_db_connection),
) -> PostgresRefreshTokenRepository:
    return PostgresRefreshTokenRepository(db)


def get_login_use_case(
    user_repo=Depends(get_user_repository),
    token_repo=Depends(get_refresh_token_repository),
) -> LoginUseCase:
    return LoginUseCase(user_repo=user_repo, token_repo=token_repo)


def get_refresh_use_case(
    token_repo=Depends(get_refresh_token_repository),
) -> RefreshUseCase:
    return RefreshUseCase(token_repo=token_repo)


def get_logout_use_case(
    token_repo=Depends(get_refresh_token_repository),
) -> LogoutUseCase:
    return LogoutUseCase(token_repo=token_repo)
```

- [ ] **Step 2: Include auth router in `backend/interface/routers/__init__.py`**

```python
from fastapi import APIRouter

from backend.interface.routers.auth import router as auth_router
from backend.interface.routers.data_contract import router as data_contract_router
from backend.interface.routers.data_product import router as data_product_router
from backend.interface.routers.users import router as users_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/api/v1", tags=["Auth"])
api_router.include_router(users_router, prefix="/api/v1", tags=["Users"])
api_router.include_router(
    data_contract_router, prefix="/api/v1", tags=["Data Contracts"]
)
api_router.include_router(data_product_router, prefix="/api/v1", tags=["Data Products"])
```

- [ ] **Step 3: Commit**

```bash
git add backend/interface/dependencies.py backend/interface/routers/__init__.py
git commit -m "feat: wire auth use cases into dependencies and register auth router"
```

---

## Task 16: Protect Existing Endpoints + Swagger HTTPBearer

**Files:**
- Modify: `backend/interface/routers/users.py`
- Modify: `backend/interface/routers/data_contract.py`
- Modify: `backend/interface/routers/data_product.py`
- Modify: `backend/main.py`

- [ ] **Step 1: Add `get_current_user` to users router**

In `backend/interface/routers/users.py`, add this import:

```python
from backend.interface.security import get_current_user
```

Add `_: User = Depends(get_current_user)` as a parameter to every route handler. Example for `list_users`:

```python
@router.get("/users", response_model=List[UserResponseModel])
async def list_users(
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
    _: User = Depends(get_current_user),
):
    users = await use_case.execute()
    return [_to_response(u) for u in users]
```

Apply the same pattern to: `create_user`, `get_user`, `update_user`, `delete_user`.

Full updated `backend/interface/routers/users.py`:

```python
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.domain.entities.user import User
from backend.interface.dependencies import (
    get_create_user_use_case,
    get_delete_user_use_case,
    get_get_user_use_case,
    get_list_users_use_case,
    get_update_user_use_case,
)
from backend.interface.schemas.user import (
    UserCreateModel,
    UserResponseModel,
    UserUpdateModel,
)
from backend.interface.security import get_current_user
from backend.use_cases.user.create import CreateUserUseCase
from backend.use_cases.user.delete import DeleteUserUseCase
from backend.use_cases.user.get import GetUserUseCase
from backend.use_cases.user.list import ListUsersUseCase
from backend.use_cases.user.update import UpdateUserUseCase

router = APIRouter()


def _to_response(user: User) -> UserResponseModel:
    return UserResponseModel(id=user.id, username=user.name, email=str(user.email))


@router.post("/users", response_model=UserResponseModel, status_code=201)
async def create_user(
    body: UserCreateModel,
    use_case: CreateUserUseCase = Depends(get_create_user_use_case),
    _: User = Depends(get_current_user),
):
    try:
        user = await use_case.execute(name=body.username, email=body.email, password=body.password)
        return _to_response(user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users", response_model=List[UserResponseModel])
async def list_users(
    use_case: ListUsersUseCase = Depends(get_list_users_use_case),
    _: User = Depends(get_current_user),
):
    users = await use_case.execute()
    return [_to_response(u) for u in users]


@router.get("/users/{user_id}", response_model=UserResponseModel)
async def get_user(
    user_id: uuid.UUID,
    use_case: GetUserUseCase = Depends(get_get_user_use_case),
    _: User = Depends(get_current_user),
):
    user = await use_case.execute(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_response(user)


@router.put("/users/{user_id}", response_model=UserResponseModel)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdateModel,
    use_case: UpdateUserUseCase = Depends(get_update_user_use_case),
    _: User = Depends(get_current_user),
):
    try:
        user = await use_case.execute(
            user_id=user_id, name=body.username, email=body.email
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_response(user)


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    use_case: DeleteUserUseCase = Depends(get_delete_user_use_case),
    _: User = Depends(get_current_user),
):
    deleted = await use_case.execute(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
```

- [ ] **Step 2: Add `get_current_user` to data_contract and data_product routers**

In `backend/interface/routers/data_contract.py`, add this import and apply to every route:

```python
from backend.interface.security import get_current_user
from backend.domain.entities.user import User
```

Add `_: User = Depends(get_current_user)` as a parameter to every route handler in that file.

Repeat the same for `backend/interface/routers/data_product.py`.

- [ ] **Step 3: Add HTTPBearer security scheme to `backend/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from backend.infra.config import CORS_ORIGINS
from backend.interface.routers import api_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title="Data Mesh Platform API",
        version="0.1.0",
        routes=app.routes,
    )
    schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in schema.get("paths", {}).values():
        for operation in path.values():
            operation.setdefault("security", [{"BearerAuth": []}])
    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi
```

- [ ] **Step 4: Start the server and verify Swagger**

```bash
uvicorn backend.main:app --reload
```

Open `http://localhost:8000/docs` — you should see:
- An **Authorize** button (🔒) in the top right of the Swagger UI
- `POST /api/v1/auth/login` endpoint with no lock icon (public)
- All other endpoints with a lock icon (protected)

- [ ] **Step 5: Commit**

```bash
git add backend/main.py backend/interface/routers/users.py backend/interface/routers/data_contract.py backend/interface/routers/data_product.py
git commit -m "feat: protect all existing endpoints with JWT auth and add Swagger HTTPBearer scheme"
```

---

## Task 17: End-to-End Swagger Smoke Test

This task verifies the full flow manually via Swagger UI at `http://localhost:8000/docs`.

- [ ] **Step 1: Create a user**

`POST /api/v1/users` — click the lock icon, use a valid token (or temporarily remove auth from this endpoint for bootstrapping). Body:
```json
{
  "username": "Alice",
  "email": "alice@example.com",
  "password": "Str0ng!Pass1"
}
```
Expected: `201` with user object.

> **Bootstrapping note:** For the very first user, you may need to insert directly into the DB:
> ```sql
> -- generate hash first in Python:
> -- import bcrypt; print(bcrypt.hashpw(b"Str0ng!Pass1", bcrypt.gensalt()).decode())
> INSERT INTO iam.users (name, email, password_hash)
> VALUES ('Alice', 'alice@example.com', '<hash>');
> ```

- [ ] **Step 2: Login**

`POST /api/v1/auth/login`. Body:
```json
{
  "email": "alice@example.com",
  "password": "Str0ng!Pass1"
}
```
Expected: `200` with `access_token` and `refresh_token`.

- [ ] **Step 3: Authorize in Swagger**

Click the **Authorize** button → paste the `access_token` → click **Authorize**.

- [ ] **Step 4: Call a protected endpoint**

`GET /api/v1/users` — Expected: `200` with user list.

- [ ] **Step 5: Refresh the token**

`POST /api/v1/auth/refresh`. Body:
```json
{ "refresh_token": "<your_refresh_token>" }
```
Expected: `200` with a new `access_token`.

- [ ] **Step 6: Logout**

`POST /api/v1/auth/logout`. Body:
```json
{ "refresh_token": "<your_refresh_token>" }
```
Expected: `200 {"detail": "Successfully logged out"}`.

- [ ] **Step 7: Verify refresh token is revoked**

Repeat Step 5 with the same refresh token.
Expected: `401 {"detail": "Invalid refresh token"}`.

- [ ] **Step 8: Run all unit tests**

```bash
pytest tests/unit/ -v
```

Expected: all tests pass.

- [ ] **Step 9: Final commit**

```bash
git add .
git commit -m "feat: complete JWT auth implementation with Swagger login"
```
