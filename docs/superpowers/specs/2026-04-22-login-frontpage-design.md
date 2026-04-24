# Login Frontpage Design

**Date:** 2026-04-22
**Branch:** feature/login-frontpage
**Status:** Approved — ready for implementation

---

## Overview

A modern login/register page for the Data Mesh Platform frontend. Users can sign in with existing credentials or create a new account from the same page. On successful auth the user lands on `/dashboard`. All existing platform routes require authentication and redirect to `/login` when unauthenticated.

---

## Visual Design

**Style:** Dark Glassmorphism

- **Background:** Full-screen gradient (`#0d0d1a → #1a0a2e → #0d1a2e`), two static radial glow orbs — indigo top-right, purple bottom-left
- **Card:** Centered, `backdrop-filter: blur(20px)`, `rgba(255,255,255,0.05)` fill, `1px solid rgba(255,255,255,0.1)` border, `border-radius: 20px`
- **Accent colors:** Indigo `#6366f1` → Purple `#a855f7` gradient on buttons and active states
- **Typography:** System font stack, white on dark

**Card contents (top to bottom):**
1. Logo row — gradient square icon + "DataMesh" wordmark
2. Pill toggle — `Sign In | Register`, switches form with opacity/translate transition
3. Form (React Hook Form + Zod)
4. Submit button — gradient, full width, spinner while loading
5. Error banner — inline, inside card, red tint on API errors

---

## Architecture

### New files

| File | Purpose |
|---|---|
| `frontend/src/contexts/AuthContext.tsx` | Global auth state — user object, access token, `login()`, `logout()` |
| `frontend/src/components/PrivateRoute.tsx` | Route guard — redirects unauthenticated users to `/login` |
| `frontend/src/pages/Login.tsx` | Full login/register page component |
| `frontend/src/lib/auth.ts` | localStorage helpers — `getToken()`, `setTokens()`, `clearTokens()` |

### Modified files

| File | Change |
|---|---|
| `frontend/src/App.tsx` | Wrap in `<AuthProvider>`, add `/login` route, wrap existing routes in `<PrivateRoute>` |
| `frontend/src/lib/api.ts` | Add `Authorization` header, 401 interceptor with singleton refresh logic |

### No backend changes required

`POST /api/v1/auth/login` and `POST /api/v1/users` are already public endpoints. No new backend routes needed.

---

## Data Flow

### Login

1. User submits email + password
2. `POST /api/v1/auth/login` → `{ access_token, refresh_token, token_type }`
3. Both tokens written to `localStorage` via `auth.ts`
4. `AuthContext` decodes the JWT `sub` claim to extract `user_id`
5. Calls `GET /api/v1/users/{user_id}` (with the new access token) to fetch full user object (name, email)
6. Stores user object in context state
7. Redirect to `/dashboard` (or saved `redirect` param — relative paths only)

### Register

1. User submits username + email + password + confirm password
2. Zod validates confirm password matches (client-side only)
3. `POST /api/v1/users` creates the account
4. On success, immediately calls `POST /api/v1/auth/login` with same credentials
5. Continues as Login flow from step 3 onward — user lands on `/dashboard` without extra steps

### Token Refresh (transparent)

1. Any API call returns `401`
2. `api.ts` interceptor checks if a refresh is already in-flight
3. If yes — queues the retry behind the existing refresh promise (singleton pattern)
4. If no — calls `POST /api/v1/auth/refresh` with stored refresh token
5. On success — stores new access token, retries all queued requests
6. On failure — clears localStorage, resets AuthContext, redirects to `/login`

### Logout

1. `POST /api/v1/auth/logout` with current access token (server revokes refresh token)
2. `clearTokens()` clears localStorage
3. AuthContext resets to unauthenticated state
4. Redirect to `/login`

---

## Form Fields & Validation

### Sign In form

| Field | Validation |
|---|---|
| Email | Required, valid email format |
| Password | Required, min 8 chars |

### Register form

| Field | Validation |
|---|---|
| Username | Required, min 2 chars |
| Email | Required, valid email format |
| Password | Required, min 8 chars |
| Confirm Password | Required, must match Password |

All validation via Zod schema, error messages displayed inline under each field.

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Wrong email/password | Error banner inside card: "Invalid email or password" |
| Email already taken (register) | Error banner: "An account with this email already exists" |
| Passwords don't match | Inline Zod error under Confirm Password |
| Network error | Error banner: "Something went wrong. Please try again." |
| Session expired | Silent redirect to `/login`, tokens cleared |
| Accessing protected route unauthenticated | `PrivateRoute` redirects to `/login?redirect=/original-path` |

---

## Security

### Token storage — localStorage (accepted trade-off)

Access tokens are stored in `localStorage`. This is readable by JavaScript and is the primary XSS attack vector. This trade-off is accepted because:
- Access tokens expire in 15 minutes
- Refresh tokens are stored as SHA-256 hashes server-side and can be individually revoked
- Migrating to `httpOnly` cookies is documented as a future improvement (see `docs/security/auth-security-roadmap.md`)

### Refresh race condition — singleton promise

Multiple simultaneous `401` responses must not each trigger a separate refresh call (the backend rotates the refresh token on use — the second call would invalidate the first's result). `api.ts` uses a module-level `refreshPromise` variable: when a refresh is in-flight, all new 401s wait on the same promise instead of starting a new one.

### Open redirect prevention

After login, the app reads `?redirect=` from the URL to send the user to their original destination. Before using this value, it is validated to be a relative path (must start with `/` and not `//`). External URLs are discarded and the user falls back to `/dashboard`.

### Rate limiting — future backend work

The `POST /api/v1/auth/login` endpoint has no brute-force protection. Documented as a future backend improvement in `docs/security/auth-security-roadmap.md`.

---

## Route Structure (App.tsx)

```
<AuthProvider>
  <Router>
    <Route path="/login" element={<Login />} />         ← public
    <Route element={<PrivateRoute />}>                  ← auth guard
      <Route path="/" element={<Layout />}>
        <Route index element={<Dashboard />} />
        <Route path="data-contracts/*" element={...} />
        <Route path="data-products/*" element={...} />
        <Route path="users/*" element={...} />
      </Route>
    </Route>
  </Router>
</AuthProvider>
```
