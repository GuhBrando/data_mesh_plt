# Login via Swagger — Design Spec

**Date:** 2026-04-20
**Status:** Approved

---

## Overview

Implement JWT Bearer token authentication for the FastAPI backend, exposing login via the Swagger UI Authorize button. All existing endpoints will be protected. The implementation follows the existing clean/hexagonal architecture pattern.

---

## Decisions

| Topic | Decision | Rationale |
|---|---|---|
| Auth type | JWT Bearer token | Standard, stateless, Swagger-native |
| Token strategy | Access + Refresh tokens | Short-lived access (15min), revocable refresh (7 days) |
| Refresh token storage | PostgreSQL (`iam.refresh_tokens`) | Enables server-side revocation; no new infra |
| Login identifier | Email | Matches existing `iam.users` schema |
| Password hashing | `bcrypt` standalone | Actively maintained, no CVEs, industry standard |
| JWT library | `PyJWT 2.12.1` | Replaces `python-jose` (CVE-2024-33663 history) |
| Endpoint protection | All existing routes | `/api/v1/users`, `/api/v1/data-contracts`, `/api/v1/data-products` |

---

## Libraries

Add to `pyproject.toml`:
- `PyJWT>=2.12.1` — JWT encode/decode
- `bcrypt>=5.0.0` — password hashing

Remove if present:
- `python-jose` — has CVE-2024-33663 (critical) history
- `passlib` — unmaintained since 2020

---

## Database Schema Evolution

**Migration file:** `database/migrations/20260420000001_add_auth.sql`

```sql
-- Add password hash to existing users
ALTER TABLE iam.users ADD COLUMN password_hash TEXT NOT NULL DEFAULT '';
ALTER TABLE iam.users ALTER COLUMN password_hash DROP DEFAULT;

-- Refresh tokens table
CREATE TABLE iam.refresh_tokens (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES iam.users(id) ON DELETE CASCADE,
    token_hash   TEXT NOT NULL,
    expires_at   TIMESTAMPTZ NOT NULL,
    revoked      BOOLEAN NOT NULL DEFAULT false,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_refresh_tokens_user_id ON iam.refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_token_hash ON iam.refresh_tokens(token_hash);
```

**Why `token_hash` and not the raw token:** If the `refresh_tokens` table is breached, raw tokens are not exposed — attacker gets SHA-256 hashes only.

**Why SHA-256 and not bcrypt for refresh tokens:** Refresh tokens are already high-entropy random strings (not user-chosen weak passwords), so SHA-256 is sufficient protection. bcrypt is impractical here because its random salt makes direct DB lookups impossible — you'd have to fetch every user token and check each one individually.

---

## Architecture

### New Files

```
backend/
├── domain/
│   └── entities/
│       └── refresh_token.py        # RefreshToken entity
├── infra/
│   ├── models/
│   │   └── refresh_token.py        # asyncpg raw SQL queries
│   └── repositories/
│       └── refresh_token.py        # RefreshTokenRepository
├── use_cases/
│   └── auth/
│       ├── login.py                # LoginUseCase
│       ├── refresh.py              # RefreshUseCase
│       └── logout.py              # LogoutUseCase
├── interface/
│   ├── routers/
│   │   └── auth.py                 # Auth endpoints
│   ├── schemas/
│   │   └── auth.py                 # LoginRequest, TokenResponse
│   └── security.py                 # JWT helpers, get_current_user dependency
└── main.py                         # Add auth router + HTTPBearer security scheme
```

### Modified Files

- `backend/main.py` — register auth router, add `HTTPBearer` security scheme for Swagger
- `backend/interface/routers/users.py` — add `Depends(get_current_user)` to all routes
- `backend/interface/routers/data_contracts.py` — add `Depends(get_current_user)` to all routes
- `backend/interface/routers/data_products.py` — add `Depends(get_current_user)` to all routes
- `backend/interface/schemas/user.py` — add password policy validator to `UserCreate`

---

## API Endpoints

| Method | Path | Auth required | Description |
|---|---|---|---|
| POST | `/api/v1/auth/login` | No | Email + password → access + refresh tokens |
| POST | `/api/v1/auth/refresh` | No | Refresh token → new access token |
| POST | `/api/v1/auth/logout` | Yes | Revoke refresh token |

---

## Data Flow

### Login
```
POST /api/v1/auth/login {email, password}
  → LoginUseCase
      → fetch user by email from iam.users
      → bcrypt.checkpw(password, user.password_hash)
      → if invalid: raise 401 "Invalid credentials"
      → generate access JWT (15min, signed with JWT_SECRET_KEY)
      → generate refresh JWT (7 days, signed with JWT_SECRET_KEY)
      → sha256(refresh_token) → store hash in iam.refresh_tokens
      → return {access_token, refresh_token, token_type: "bearer"}
```

### Protected Request
```
GET /api/v1/data-products
  Header: Authorization: Bearer <access_token>
  → get_current_user(Depends)
      → PyJWT.decode(token, JWT_SECRET_KEY)
      → if expired/invalid: raise 401
      → fetch user from DB
      → inject User into route handler
```

### Refresh
```
POST /api/v1/auth/refresh {refresh_token}
  → RefreshUseCase
      → PyJWT.decode(refresh_token, JWT_SECRET_KEY)
      → lookup token hash in iam.refresh_tokens
      → if revoked or not found: raise 401
      → issue new access JWT (15min)
      → return {access_token, token_type: "bearer"}
```

### Logout
```
POST /api/v1/auth/logout {refresh_token}
  → LogoutUseCase
      → lookup token hash in iam.refresh_tokens
      → SET revoked = true
      → return 200
```

---

## Password Policy

Enforced via Pydantic validator on `UserCreate.password`:

- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 number
- At least 1 special character (`!@#$%^&*`)

Violation returns `422` with a descriptive message.

---

## Environment Variables

Add to `.env`:
```
JWT_SECRET_KEY=<long random string, never commit>
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

**Security notes:**
- Rotating `JWT_SECRET_KEY` immediately invalidates all active tokens (forces re-login)
- Does NOT affect stored passwords — bcrypt hashes are independent
- If DB is breached: force password resets (key rotation alone is insufficient)

---

## Error Handling

| Scenario | Status | Message |
|---|---|---|
| Wrong email or password | 401 | `"Invalid credentials"` (same for both — never reveal which field failed) |
| Expired access token | 401 | `"Token expired"` |
| Invalid/malformed token | 401 | `"Could not validate credentials"` |
| Revoked/expired refresh token | 401 | `"Invalid refresh token"` |
| Missing Authorization header | 401 | `"Not authenticated"` |
| Weak password on register | 422 | `"Password must be at least 8 characters..."` |

---

## Swagger UX

- `main.py` registers `HTTPBearer` security scheme
- Swagger UI at `/docs` shows an **Authorize** button
- User clicks Authorize → pastes `access_token` → all subsequent Swagger requests include `Authorization: Bearer <token>` automatically
- After 15 minutes the token expires → user hits `/auth/login` again to get a fresh token

---

## Testing

### Unit Tests
- `LoginUseCase` — wrong email, wrong password, valid credentials
- bcrypt hash/verify roundtrip
- JWT encode → decode → correct claims
- Expired token raises correct error
- Password policy validator rejects weak passwords

### Integration Tests
- `POST /auth/login` → returns valid access + refresh tokens
- `GET /api/v1/data-products` without token → 401
- `GET /api/v1/data-products` with valid token → 200
- `POST /auth/refresh` → new access token issued
- `POST /auth/logout` → refresh token revoked
- `POST /auth/refresh` after logout → 401

---

## Out of Scope

- Rate limiting on `/auth/login` (brute force protection — add later via middleware)
- Password reset flow
- Email verification on registration
- Role-based access control (RBAC)
