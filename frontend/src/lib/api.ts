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
        if (Array.isArray(body.detail)) {
          message = body.detail
            .map((e: { msg?: string }) =>
              (e.msg ?? 'Validation error').replace(/^Value error,\s*/i, ''),
            )
            .join('. ')
        } else if (typeof body.detail === 'string') {
          message = body.detail
        }
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

export async function getText(path: string): Promise<string> {
  const res = await fetchWithRetry(`${BASE_URL}${path}`, { method: 'GET' })
  if (!res.ok) {
    throw new ApiError(res.status, `HTTP error ${res.status}`)
  }
  return res.text()
}
