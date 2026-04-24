# Login Frontpage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dark glassmorphism login/register page with AuthContext + PrivateRoute so all existing platform routes require authentication.

**Architecture:** `AuthContext` (React Context) holds user and token state, restoring session from `localStorage` on mount. A `PrivateRoute` outlet component guards all existing routes. The `api.ts` HTTP client injects the Bearer token on every request and handles transparent token refresh with a singleton promise to avoid race conditions.

**Tech Stack:** React 18, TypeScript, React Router 6, React Hook Form 7, Zod 3, TailwindCSS 3, Lucide React, Vitest, @testing-library/react

---

## File Map

| Action | Path | Responsibility |
|---|---|---|
| Create | `frontend/src/lib/auth.ts` | localStorage token helpers + JWT decode + redirect guard |
| Create | `frontend/src/test/setup.ts` | Vitest global test setup |
| Create | `frontend/src/contexts/AuthContext.tsx` | Global auth state (user, isLoading, setUser, logout) |
| Create | `frontend/src/components/PrivateRoute.tsx` | Route guard — redirects unauthenticated users |
| Create | `frontend/src/pages/Login.tsx` | Full login/register page |
| Modify | `frontend/src/lib/api.ts` | Add Authorization header + 401 refresh interceptor |
| Modify | `frontend/src/App.tsx` | Add AuthProvider, /login route, PrivateRoute wrapper |
| Modify | `frontend/src/components/Sidebar.tsx` | Add logout button |
| Modify | `frontend/vite.config.ts` | Add vitest config |
| Modify | `frontend/package.json` | Add test dependencies and scripts |

---

## Task 1: Set up Vitest for frontend testing

**Files:**
- Modify: `frontend/package.json`
- Modify: `frontend/vite.config.ts`
- Create: `frontend/src/test/setup.ts`

- [ ] **Step 1: Install test dependencies**

Run from `frontend/` directory:
```bash
cd frontend
npm install --save-dev vitest jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event @types/node
```

Expected: packages added to `devDependencies`, no errors.

- [ ] **Step 2: Add test scripts to package.json**

In `frontend/package.json`, add to `"scripts"`:
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

- [ ] **Step 3: Add vitest config to vite.config.ts**

Replace `frontend/vite.config.ts` with:
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_BACKEND_URL ?? 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.ts',
  },
})
```

- [ ] **Step 4: Create test setup file**

Create `frontend/src/test/setup.ts`:
```ts
import '@testing-library/jest-dom'
```

- [ ] **Step 5: Verify setup works**

```bash
cd frontend && npm test
```

Expected: `No test files found` (not an error — means vitest ran successfully with zero test files).

- [ ] **Step 6: Commit**

```bash
cd frontend
git add package.json vite.config.ts src/test/setup.ts package-lock.json
git commit -m "chore: set up vitest with jsdom and @testing-library/react"
```

---

## Task 2: Create `auth.ts` — localStorage helpers

**Files:**
- Create: `frontend/src/lib/auth.ts`
- Create: `frontend/src/lib/auth.test.ts`

- [ ] **Step 1: Write the failing tests**

Create `frontend/src/lib/auth.test.ts`:
```ts
import { describe, it, expect, beforeEach } from 'vitest'
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  decodeJwtPayload,
  isSafeRedirect,
} from './auth'

describe('token storage', () => {
  beforeEach(() => localStorage.clear())

  it('returns null when no tokens stored', () => {
    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })

  it('stores and retrieves both tokens', () => {
    setTokens('acc-123', 'ref-456')
    expect(getAccessToken()).toBe('acc-123')
    expect(getRefreshToken()).toBe('ref-456')
  })

  it('clears both tokens', () => {
    setTokens('acc-123', 'ref-456')
    clearTokens()
    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })
})

describe('decodeJwtPayload', () => {
  it('decodes the payload segment', () => {
    const payload = btoa(JSON.stringify({ sub: 'user-abc', exp: 9_999_999_999 }))
    const token = `header.${payload}.sig`
    const result = decodeJwtPayload(token)
    expect(result.sub).toBe('user-abc')
    expect(result.exp).toBe(9_999_999_999)
  })

  it('handles URL-safe base64 characters', () => {
    // base64url uses - and _ instead of + and /
    const raw = JSON.stringify({ sub: 'u', exp: 1 })
    // manually create a base64url payload
    const payload = btoa(raw).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
    const token = `h.${payload}.s`
    const result = decodeJwtPayload(token)
    expect(result.sub).toBe('u')
  })
})

describe('isSafeRedirect', () => {
  it('allows relative paths', () => {
    expect(isSafeRedirect('/dashboard')).toBe(true)
    expect(isSafeRedirect('/data-contracts/123')).toBe(true)
    expect(isSafeRedirect('/')).toBe(true)
  })

  it('rejects protocol-relative URLs', () => {
    expect(isSafeRedirect('//evil.com')).toBe(false)
  })

  it('rejects absolute URLs', () => {
    expect(isSafeRedirect('https://evil.com')).toBe(false)
    expect(isSafeRedirect('http://evil.com/path')).toBe(false)
  })

  it('rejects empty string and non-strings', () => {
    expect(isSafeRedirect('')).toBe(false)
    expect(isSafeRedirect(null as unknown as string)).toBe(false)
  })
})
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd frontend && npm test
```

Expected: FAIL — `Cannot find module './auth'`

- [ ] **Step 3: Implement auth.ts**

Create `frontend/src/lib/auth.ts`:
```ts
const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setTokens(accessToken: string, refreshToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
}

export function decodeJwtPayload(token: string): { sub: string; exp: number } {
  const segment = token.split('.')[1]
  const padded = segment.replace(/-/g, '+').replace(/_/g, '/').padEnd(
    segment.length + ((4 - (segment.length % 4)) % 4),
    '=',
  )
  return JSON.parse(atob(padded))
}

export function isSafeRedirect(url: unknown): url is string {
  return typeof url === 'string' && url.length > 0 && url.startsWith('/') && !url.startsWith('//')
}
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd frontend && npm test
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/auth.ts frontend/src/lib/auth.test.ts
git commit -m "feat: add auth token storage helpers with tests"
```

---

## Task 3: Update `api.ts` — auth header + singleton refresh interceptor

**Files:**
- Modify: `frontend/src/lib/api.ts`

The existing `api.ts` adds no auth header and has no 401 handling. Replace it entirely with a version that:
1. Reads the access token and sends `Authorization: Bearer <token>` on every request
2. On 401 — if a refresh token exists, calls `POST /auth/refresh` once (singleton promise) and retries
3. On refresh failure — clears tokens and dispatches `auth:logout` custom event (AuthContext listens to this)
4. On 401 with no refresh token — returns the 401 response as-is (handles login/register errors correctly)

- [ ] **Step 1: Replace api.ts**

Write `frontend/src/lib/api.ts`:
```ts
import { getAccessToken, getRefreshToken, setTokens, clearTokens } from './auth'

const BASE_URL = (import.meta.env.VITE_API_URL ?? '') + '/api/v1'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let message = `HTTP error ${res.status}`
    try {
      const body = await res.json()
      if (body?.detail) {
        message = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail)
      } else if (body?.message) {
        message = body.message
      }
    } catch {
      // non-JSON error body — keep generic message
    }
    throw new ApiError(res.status, message)
  }

  if (res.status === 204) return undefined as unknown as T
  return res.json() as Promise<T>
}

function buildHeaders(token?: string | null): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  }
  const t = token ?? getAccessToken()
  if (t) headers['Authorization'] = `Bearer ${t}`
  return headers
}

let refreshPromise: Promise<string> | null = null

async function doRefresh(): Promise<string> {
  if (refreshPromise) return refreshPromise
  refreshPromise = (async () => {
    const refreshToken = getRefreshToken()
    if (!refreshToken) throw new Error('No refresh token')
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
    if (!res.ok) throw new Error('Refresh failed')
    const data = await res.json() as { access_token: string }
    setTokens(data.access_token, refreshToken)
    return data.access_token
  })().finally(() => {
    refreshPromise = null
  })
  return refreshPromise
}

async function fetchWithRetry(url: string, init: RequestInit): Promise<Response> {
  const res = await fetch(url, { ...init, headers: buildHeaders() })
  if (res.status !== 401) return res

  // No refresh token means we're on a public endpoint (login, register).
  // Return the 401 as-is so handleResponse can surface the correct error message.
  if (!getRefreshToken()) return res

  try {
    const newToken = await doRefresh()
    return fetch(url, { ...init, headers: buildHeaders(newToken) })
  } catch {
    clearTokens()
    window.dispatchEvent(new CustomEvent('auth:logout'))
    throw new ApiError(401, 'Session expired. Please sign in again.')
  }
}

export async function get<T>(path: string): Promise<T> {
  const res = await fetchWithRetry(`${BASE_URL}${path}`, { method: 'GET' })
  return handleResponse<T>(res)
}

export async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetchWithRetry(`${BASE_URL}${path}`, {
    method: 'POST',
    body: JSON.stringify(body),
  })
  return handleResponse<T>(res)
}

export async function put<T>(path: string, body: unknown): Promise<T> {
  const res = await fetchWithRetry(`${BASE_URL}${path}`, {
    method: 'PUT',
    body: JSON.stringify(body),
  })
  return handleResponse<T>(res)
}

export async function del(path: string): Promise<void> {
  const res = await fetchWithRetry(`${BASE_URL}${path}`, { method: 'DELETE' })
  await handleResponse<void>(res)
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat: add bearer token injection and singleton refresh interceptor to api client"
```

---

## Task 4: Create `AuthContext.tsx`

**Files:**
- Create: `frontend/src/contexts/AuthContext.tsx`

AuthContext holds `user`, `isLoading`, `setUser`, and `logout`. On mount it checks for a stored access token, decodes the user ID, and fetches the full user object. It also listens for the `auth:logout` custom event dispatched by `api.ts` when a refresh fails.

- [ ] **Step 1: Create AuthContext.tsx**

Create `frontend/src/contexts/AuthContext.tsx`:
```tsx
import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react'
import { getAccessToken, clearTokens, decodeJwtPayload } from '../lib/auth'
import { get } from '../lib/api'
import type { User } from '../types'

interface AuthContextValue {
  user: User | null
  isLoading: boolean
  setUser: (user: User | null) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  isLoading: true,
  setUser: () => {},
  logout: () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const logout = useCallback(() => {
    clearTokens()
    setUser(null)
  }, [])

  // Restore session from localStorage on mount
  useEffect(() => {
    const token = getAccessToken()
    if (!token) {
      setIsLoading(false)
      return
    }
    let cancelled = false
    try {
      const { sub } = decodeJwtPayload(token)
      get<User>(`/users/${sub}`)
        .then((u) => { if (!cancelled) setUser(u) })
        .catch(() => { if (!cancelled) clearTokens() })
        .finally(() => { if (!cancelled) setIsLoading(false) })
    } catch {
      clearTokens()
      setIsLoading(false)
    }
    return () => { cancelled = true }
  }, [])

  // Listen for forced logout dispatched by api.ts when refresh fails
  useEffect(() => {
    window.addEventListener('auth:logout', logout)
    return () => window.removeEventListener('auth:logout', logout)
  }, [logout])

  return (
    <AuthContext.Provider value={{ user, isLoading, setUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/contexts/AuthContext.tsx
git commit -m "feat: add AuthContext with session restore and forced-logout listener"
```

---

## Task 5: Create `PrivateRoute.tsx`

**Files:**
- Create: `frontend/src/components/PrivateRoute.tsx`

Shows a centered spinner while auth state loads. Redirects unauthenticated users to `/login?redirect=<original-path>`. Renders the nested `<Outlet />` for authenticated users.

- [ ] **Step 1: Create PrivateRoute.tsx**

Create `frontend/src/components/PrivateRoute.tsx`:
```tsx
import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function PrivateRoute() {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center min-h-screen"
        style={{ background: 'linear-gradient(135deg, #0d0d1a 0%, #1a0a2e 40%, #0d1a2e 100%)' }}
      >
        <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
      </div>
    )
  }

  if (!user) {
    return (
      <Navigate
        to={`/login?redirect=${encodeURIComponent(location.pathname)}`}
        replace
      />
    )
  }

  return <Outlet />
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/PrivateRoute.tsx
git commit -m "feat: add PrivateRoute component with loading spinner and redirect"
```

---

## Task 6: Create `Login.tsx` — the login/register page

**Files:**
- Create: `frontend/src/pages/Login.tsx`

Full page with dark glassmorphism background, centered glass card, pill toggle between Sign In and Register, React Hook Form + Zod validation, and inline error banner.

- [ ] **Step 1: Create Login.tsx**

Create `frontend/src/pages/Login.tsx`:
```tsx
import React, { useState } from 'react'
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Loader2 } from 'lucide-react'
import { post, get } from '../lib/api'
import { setTokens, isSafeRedirect, decodeJwtPayload } from '../lib/auth'
import { useAuth } from '../contexts/AuthContext'
import type { User } from '../types'

// ─── Schemas ─────────────────────────────────────────────────────────────────

const signInSchema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

const registerSchema = z
  .object({
    username: z.string().min(2, 'Username must be at least 2 characters'),
    email: z.string().email('Enter a valid email'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string(),
  })
  .refine((d) => d.password === d.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

type SignInValues = z.infer<typeof signInSchema>
type RegisterValues = z.infer<typeof registerSchema>

// ─── Helpers ─────────────────────────────────────────────────────────────────

interface LoginApiResponse {
  access_token: string
  refresh_token: string
}

async function performLogin(email: string, password: string): Promise<User> {
  const { access_token, refresh_token } = await post<LoginApiResponse>(
    '/auth/login',
    { email, password },
  )
  setTokens(access_token, refresh_token)
  const { sub } = decodeJwtPayload(access_token)
  return get<User>(`/users/${sub}`)
}

// ─── Sub-components ───────────────────────────────────────────────────────────

const GlassInput = React.forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement> & { hasError?: boolean }
>(({ hasError, className, ...props }, ref) => (
  <input
    ref={ref}
    {...props}
    className={`w-full bg-transparent outline-none text-sm text-white ${className ?? ''}`}
    style={{
      padding: '10px 14px',
      border: hasError
        ? '1px solid rgba(239,68,68,0.5)'
        : '1px solid rgba(255,255,255,0.1)',
      borderRadius: '10px',
      background: 'rgba(255,255,255,0.07)',
    }}
  />
))
GlassInput.displayName = 'GlassInput'

function GlassField({
  label,
  error,
  children,
}: {
  label: string
  error?: string
  children: React.ReactNode
}) {
  return (
    <div className="mb-4">
      <label
        className="block text-xs font-medium mb-1.5"
        style={{ color: 'rgba(255,255,255,0.6)' }}
      >
        {label}
      </label>
      {children}
      {error && (
        <p className="mt-1 text-xs" style={{ color: '#f87171' }}>
          {error}
        </p>
      )}
    </div>
  )
}

function GlassButton({
  children,
  loading,
}: {
  children: React.ReactNode
  loading: boolean
}) {
  return (
    <button
      type="submit"
      disabled={loading}
      className="w-full flex items-center justify-center gap-2 py-2.5 mt-2 text-sm font-semibold text-white transition-opacity disabled:opacity-70"
      style={{
        background: 'linear-gradient(135deg, #6366f1, #a855f7)',
        borderRadius: '10px',
        border: 'none',
        cursor: loading ? 'not-allowed' : 'pointer',
      }}
    >
      {loading && <Loader2 size={15} className="animate-spin" />}
      {children}
    </button>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function Login() {
  const [mode, setMode] = useState<'signin' | 'register'>('signin')
  const [error, setError] = useState<string | null>(null)
  const { user, isLoading, setUser } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()

  const signInForm = useForm<SignInValues>({ resolver: zodResolver(signInSchema) })
  const registerForm = useForm<RegisterValues>({ resolver: zodResolver(registerSchema) })

  // Already authenticated — skip the login page
  if (!isLoading && user) return <Navigate to="/dashboard" replace />

  const rawRedirect = searchParams.get('redirect') ?? ''
  const redirectTo = isSafeRedirect(rawRedirect) ? rawRedirect : '/dashboard'

  function switchMode(next: 'signin' | 'register') {
    setMode(next)
    setError(null)
    signInForm.reset()
    registerForm.reset()
  }

  async function handleSignIn(values: SignInValues) {
    setError(null)
    try {
      const fetched = await performLogin(values.email, values.password)
      setUser(fetched)
      navigate(redirectTo, { replace: true })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong. Please try again.')
    }
  }

  async function handleRegister(values: RegisterValues) {
    setError(null)
    try {
      await post('/users', {
        username: values.username,
        email: values.email,
        password: values.password,
      })
      const fetched = await performLogin(values.email, values.password)
      setUser(fetched)
      navigate(redirectTo, { replace: true })
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Something went wrong. Please try again.')
    }
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center relative overflow-hidden"
      style={{
        background: 'linear-gradient(135deg, #0d0d1a 0%, #1a0a2e 40%, #0d1a2e 100%)',
      }}
    >
      {/* Glow orbs */}
      <div
        className="absolute pointer-events-none"
        style={{
          top: '-100px',
          right: '-80px',
          width: '400px',
          height: '400px',
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(99,102,241,0.25) 0%, transparent 70%)',
        }}
      />
      <div
        className="absolute pointer-events-none"
        style={{
          bottom: '-60px',
          left: '-60px',
          width: '300px',
          height: '300px',
          borderRadius: '50%',
          background:
            'radial-gradient(circle, rgba(168,85,247,0.15) 0%, transparent 70%)',
        }}
      />

      {/* Glass card */}
      <div
        className="relative z-10 w-full mx-4"
        style={{
          maxWidth: '400px',
          background: 'rgba(255,255,255,0.05)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '20px',
          padding: '40px 36px',
        }}
      >
        {/* Logo row */}
        <div className="flex items-center gap-3 mb-8">
          <div
            className="shrink-0"
            style={{
              width: '32px',
              height: '32px',
              background: 'linear-gradient(135deg, #6366f1, #a855f7)',
              borderRadius: '8px',
            }}
          />
          <span className="text-white font-bold text-lg tracking-tight">
            DataMesh
          </span>
        </div>

        {/* Pill toggle */}
        <div
          className="flex mb-7"
          style={{
            background: 'rgba(255,255,255,0.06)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '999px',
            padding: '3px',
          }}
        >
          {(['signin', 'register'] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => switchMode(m)}
              className="flex-1 py-2 text-sm font-semibold transition-all"
              style={{
                borderRadius: '999px',
                border: 'none',
                cursor: 'pointer',
                background:
                  mode === m
                    ? 'linear-gradient(135deg, #6366f1, #a855f7)'
                    : 'transparent',
                color: mode === m ? '#fff' : 'rgba(255,255,255,0.4)',
              }}
            >
              {m === 'signin' ? 'Sign In' : 'Register'}
            </button>
          ))}
        </div>

        {/* Error banner */}
        {error && (
          <div
            className="mb-5 text-sm"
            style={{
              background: 'rgba(239,68,68,0.15)',
              border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: '10px',
              padding: '12px 14px',
              color: '#fca5a5',
            }}
          >
            {error}
          </div>
        )}

        {/* Sign In form */}
        {mode === 'signin' && (
          <form onSubmit={signInForm.handleSubmit(handleSignIn)} noValidate>
            <GlassField
              label="Email"
              error={signInForm.formState.errors.email?.message}
            >
              <GlassInput
                {...signInForm.register('email')}
                type="email"
                placeholder="you@company.com"
                autoComplete="email"
                hasError={!!signInForm.formState.errors.email}
              />
            </GlassField>
            <GlassField
              label="Password"
              error={signInForm.formState.errors.password?.message}
            >
              <GlassInput
                {...signInForm.register('password')}
                type="password"
                placeholder="••••••••"
                autoComplete="current-password"
                hasError={!!signInForm.formState.errors.password}
              />
            </GlassField>
            <GlassButton loading={signInForm.formState.isSubmitting}>
              Sign In
            </GlassButton>
          </form>
        )}

        {/* Register form */}
        {mode === 'register' && (
          <form onSubmit={registerForm.handleSubmit(handleRegister)} noValidate>
            <GlassField
              label="Username"
              error={registerForm.formState.errors.username?.message}
            >
              <GlassInput
                {...registerForm.register('username')}
                type="text"
                placeholder="johndoe"
                autoComplete="username"
                hasError={!!registerForm.formState.errors.username}
              />
            </GlassField>
            <GlassField
              label="Email"
              error={registerForm.formState.errors.email?.message}
            >
              <GlassInput
                {...registerForm.register('email')}
                type="email"
                placeholder="you@company.com"
                autoComplete="email"
                hasError={!!registerForm.formState.errors.email}
              />
            </GlassField>
            <GlassField
              label="Password"
              error={registerForm.formState.errors.password?.message}
            >
              <GlassInput
                {...registerForm.register('password')}
                type="password"
                placeholder="••••••••"
                autoComplete="new-password"
                hasError={!!registerForm.formState.errors.password}
              />
            </GlassField>
            <GlassField
              label="Confirm Password"
              error={registerForm.formState.errors.confirmPassword?.message}
            >
              <GlassInput
                {...registerForm.register('confirmPassword')}
                type="password"
                placeholder="••••••••"
                autoComplete="new-password"
                hasError={!!registerForm.formState.errors.confirmPassword}
              />
            </GlassField>
            <GlassButton loading={registerForm.formState.isSubmitting}>
              Create Account
            </GlassButton>
          </form>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Login.tsx
git commit -m "feat: add dark glassmorphism login/register page"
```

---

## Task 7: Update `App.tsx` — wire AuthProvider, /login route, PrivateRoute

**Files:**
- Modify: `frontend/src/App.tsx`

`AuthProvider` wraps the router. `/login` is the only public route. All existing routes sit inside a `<PrivateRoute>` outlet.

- [ ] **Step 1: Replace App.tsx**

Write `frontend/src/App.tsx`:
```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import PrivateRoute from './components/PrivateRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import DataContractsList from './pages/DataContracts'
import DataContractDetail from './pages/DataContracts/DataContractDetail'
import DataProductsList from './pages/DataProducts'
import DataProductDetail from './pages/DataProducts/DataProductDetail'
import UsersList from './pages/Users'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<PrivateRoute />}>
            <Route path="/" element={<Layout />}>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="dashboard" element={<Dashboard />} />
              <Route path="data-contracts" element={<DataContractsList />} />
              <Route path="data-contracts/:id" element={<DataContractDetail />} />
              <Route path="data-products" element={<DataProductsList />} />
              <Route path="data-products/:id" element={<DataProductDetail />} />
              <Route path="users" element={<UsersList />} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx
git commit -m "feat: wire AuthProvider and PrivateRoute into app router"
```

---

## Task 8: Add logout button to `Sidebar.tsx`

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx`

Add a logout button at the bottom of the sidebar that calls `POST /auth/logout` (to revoke the refresh token server-side) then clears local state.

- [ ] **Step 1: Update Sidebar.tsx**

Replace `frontend/src/components/Sidebar.tsx` with:
```tsx
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  FileText,
  Package,
  Users,
  Database,
  Sun,
  Moon,
  LogOut,
} from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'
import { post } from '../lib/api'
import { getRefreshToken } from '../lib/auth'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/data-contracts', icon: FileText, label: 'Data Contracts' },
  { to: '/data-products', icon: Package, label: 'Data Products' },
  { to: '/users', icon: Users, label: 'Users' },
]

export default function Sidebar() {
  const { theme, toggle } = useTheme()
  const { user, logout } = useAuth()

  async function handleLogout() {
    try {
      const refreshToken = getRefreshToken()
      if (refreshToken) {
        await post('/auth/logout', { refresh_token: refreshToken })
      }
    } finally {
      logout()
    }
  }

  return (
    <aside className="w-64 shrink-0 bg-slate-900 min-h-screen flex flex-col">
      {/* Brand */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-slate-800">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center shrink-0">
          <Database size={16} className="text-white" />
        </div>
        <div>
          <p className="text-white font-semibold text-sm leading-tight">Data Mesh</p>
          <p className="text-slate-400 text-xs">Platform</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-0.5">
        <p className="px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">
          Navigation
        </p>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
          >
            <Icon size={16} className="shrink-0" />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-800">
        {/* User info */}
        {user && (
          <div className="flex items-center gap-2 mb-3 px-1">
            <div className="w-6 h-6 rounded-full bg-indigo-600 flex items-center justify-center shrink-0">
              <span className="text-white text-xs font-semibold">
                {user.username.charAt(0).toUpperCase()}
              </span>
            </div>
            <span className="text-slate-300 text-xs truncate">{user.username}</span>
          </div>
        )}

        <div className="flex items-center justify-between">
          <button
            onClick={handleLogout}
            className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-900/20 transition-colors text-xs"
            title="Sign out"
          >
            <LogOut size={14} />
            Sign out
          </button>
          <button
            onClick={toggle}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
          >
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        </div>
      </div>
    </aside>
  )
}
```

- [ ] **Step 2: Verify TypeScript compiles**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Sidebar.tsx
git commit -m "feat: add logout button and current user display to sidebar"
```

---

## Task 9: Manual smoke test

Start the dev server and verify each flow end-to-end.

- [ ] **Step 1: Start dev server**

```bash
cd frontend && npm run dev
```

Open `http://localhost:5173` in a browser.

- [ ] **Step 2: Verify unauthenticated redirect**

Expected: Browser immediately redirects to `http://localhost:5173/login?redirect=%2Fdashboard`. The dark glassmorphism login page appears with the pill toggle showing "Sign In | Register".

- [ ] **Step 3: Test Zod validation**

Click "Sign In". Submit the form with an empty email. Expected: "Enter a valid email" appears inline under the Email field. No API call made.

- [ ] **Step 4: Test wrong credentials**

Enter `wrong@test.com` / `wrongpassword`. Click "Sign In". Expected: Red error banner appears inside the card reading the backend's error message ("Invalid email or password" or similar). Fields remain filled.

- [ ] **Step 5: Test registration**

Toggle to "Register". Fill in:
- Username: `testuser`
- Email: `testuser@example.com`
- Password: `password123`
- Confirm Password: `password123`

Click "Create Account". Expected: Account created, auto-login fires, redirected to `/dashboard`.

- [ ] **Step 6: Test confirm password mismatch**

Toggle to "Register". Enter different values for Password and Confirm Password. Click "Create Account". Expected: "Passwords do not match" appears under the Confirm Password field. No API call.

- [ ] **Step 7: Verify authenticated state**

After successful login, sidebar shows username initial avatar and "Sign out" button. All nav links work.

- [ ] **Step 8: Test logout**

Click "Sign out" in sidebar. Expected: Redirected to `/login`. localStorage is cleared (verify in DevTools → Application → Local Storage).

- [ ] **Step 9: Test already-logged-in redirect**

Log in again. Then navigate to `http://localhost:5173/login`. Expected: Immediately redirected to `/dashboard` — the login page is skipped for authenticated users.

- [ ] **Step 10: Final commit**

```bash
cd frontend && npm test
```

Expected: All 8 auth.ts tests pass.

```bash
git add -A
git commit -m "feat: complete login frontpage — auth flow verified manually"
```
