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
  const parts = token.split('.')
  if (parts.length !== 3) throw new Error('decodeJwtPayload: invalid JWT structure')
  const segment = parts[1]
  const padded = segment.replace(/-/g, '+').replace(/_/g, '/').padEnd(
    segment.length + ((4 - (segment.length % 4)) % 4),
    '=',
  )
  return JSON.parse(atob(padded))
}

export function isSafeRedirect(url: unknown): url is string {
  return typeof url === 'string' && url.length > 0 && url.startsWith('/') && !url.startsWith('//')
}

export function isTokenExpired(token: string): boolean {
  try {
    const { exp } = decodeJwtPayload(token)
    return Date.now() / 1000 >= exp - 30
  } catch {
    return true
  }
}
