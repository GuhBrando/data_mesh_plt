# Auth Security Roadmap

Tracked security improvements that were deferred during the initial login implementation (`feature/login-frontpage`, 2026-04-22). Each item has a clear upgrade path documented below.

---

## 1. Migrate token storage from localStorage to httpOnly cookies

**Priority:** High
**Current state:** Access and refresh tokens are stored in `localStorage`. This is readable by any JavaScript on the page, making it vulnerable to XSS token theft.

**Target state:** Tokens delivered and stored in `httpOnly`, `SameSite=Strict` cookies. JavaScript cannot access these — even a successful XSS attack cannot steal them.

**Why it was deferred:** Requires coordinated backend changes that were out of scope for the initial auth UI sprint.

### Backend changes required

1. **Login endpoint** (`POST /api/v1/auth/login`) — instead of returning tokens in the JSON body, set them as cookies:
   ```
   Set-Cookie: access_token=<jwt>; HttpOnly; Secure; SameSite=Strict; Max-Age=900; Path=/
   Set-Cookie: refresh_token=<jwt>; HttpOnly; Secure; SameSite=Strict; Max-Age=604800; Path=/api/v1/auth/refresh
   ```
2. **Refresh endpoint** (`POST /api/v1/auth/refresh`) — read refresh token from cookie instead of request body.
3. **Logout endpoint** (`POST /api/v1/auth/logout`) — clear both cookies by setting `Max-Age=0`.
4. **CORS config** — add `allow_credentials=True` and restrict `allow_origins` to the exact frontend origin (wildcards are not allowed with credentials).
5. **Security middleware** — validate `Origin` header on cookie-reading endpoints to defend against CSRF (cookies are sent automatically by the browser, unlike Bearer tokens).

### Frontend changes required

1. Remove `frontend/src/lib/auth.ts` (localStorage helpers — no longer needed).
2. Remove `Authorization: Bearer` header injection from `api.ts` — cookies are sent automatically.
3. The 401 → refresh → retry logic in `api.ts` remains the same; only the storage mechanism changes.
4. Remove token parsing from `AuthContext` — fetch the current user from `GET /api/v1/users/me` (a new endpoint) instead of decoding the JWT client-side.

### New backend endpoint needed

`GET /api/v1/users/me` — returns the current authenticated user from the JWT in the cookie. Used by `AuthContext` on mount to restore session state.

---

## 2. Rate limiting on the login endpoint

**Priority:** Medium
**Current state:** `POST /api/v1/auth/login` has no brute-force protection. An attacker can try unlimited password combinations against any email address.

**Target state:** Login attempts throttled per IP and per email address, with exponential backoff and lockout.

**Why it was deferred:** Requires infrastructure-level or middleware changes out of scope for the initial auth sprint.

### Implementation options (pick one)

**Option A — FastAPI middleware with in-memory counter (simple, single instance)**
- Use `slowapi` (a FastAPI-compatible rate limiter built on `limits`):
  ```python
  # pip install slowapi
  from slowapi import Limiter
  from slowapi.util import get_remote_address

  limiter = Limiter(key_func=get_remote_address)

  @router.post("/auth/login")
  @limiter.limit("5/minute")
  async def login(request: Request, ...):
      ...
  ```
- Limit: 5 attempts per minute per IP. Returns `429 Too Many Requests`.
- Drawback: resets on process restart; doesn't work across multiple instances.

**Option B — Redis-backed rate limiter (production-grade)**
- Use `slowapi` with a Redis backend, or `redis-py` directly with a sliding window counter.
- Survives restarts, works across multiple instances.
- Requires a Redis instance (can reuse existing infra or add via Docker Compose).

**Option C — Infrastructure layer (API Gateway / reverse proxy)**
- Implement at the nginx, Caddy, or cloud API Gateway level.
- No application code changes.
- Best for multi-service deployments.

### Recommended approach

Start with **Option A** for immediate protection, migrate to **Option B** when horizontal scaling is needed.

### Additional hardening to consider alongside rate limiting

- **Account lockout:** After 10 failed attempts for a specific email, lock for 15 minutes (store counter in Redis or DB).
- **Response timing:** Ensure failed logins take the same time as successful ones (already handled by bcrypt — it runs regardless of whether the email exists).
- **Audit log:** Log failed login attempts with timestamp, IP, and email (hashed) for security monitoring.
