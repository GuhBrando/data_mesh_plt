import { describe, it, expect, beforeEach } from 'vitest'
import {
  getAccessToken,
  getRefreshToken,
  setTokens,
  clearTokens,
  decodeJwtPayload,
  isSafeRedirect,
  isTokenExpired,
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

  it('throws on malformed token', () => {
    expect(() => decodeJwtPayload('notajwt')).toThrow('invalid JWT structure')
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

describe('isTokenExpired', () => {
  it('returns false for a token that expires in the future', () => {
    const exp = Math.floor(Date.now() / 1000) + 3600
    const payload = btoa(JSON.stringify({ sub: 'u', exp }))
    const token = `h.${payload}.s`
    expect(isTokenExpired(token)).toBe(false)
  })

  it('returns true for a token that is expired', () => {
    const exp = Math.floor(Date.now() / 1000) - 60
    const payload = btoa(JSON.stringify({ sub: 'u', exp }))
    const token = `h.${payload}.s`
    expect(isTokenExpired(token)).toBe(true)
  })

  it('returns true for a malformed token', () => {
    expect(isTokenExpired('bad')).toBe(true)
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
