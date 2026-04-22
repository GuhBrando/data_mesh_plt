import {
  createContext,
  useContext,
  useEffect,
  useState,
  useCallback,
  type ReactNode,
} from 'react'
import { getAccessToken, clearTokens, decodeJwtPayload, isTokenExpired } from '../lib/auth'
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
    let cancelled = false
    const token = getAccessToken()
    if (!token || isTokenExpired(token)) {
      clearTokens()
      setIsLoading(false)
      return
    }
    try {
      const { sub } = decodeJwtPayload(token)
      get<User>(`/users/${sub}`)
        .then((u) => { if (!cancelled) setUser(u) })
        .catch(() => { if (!cancelled) clearTokens() })
        .finally(() => { if (!cancelled) setIsLoading(false) })
    } catch {
      if (!cancelled) {
        clearTokens()
        setIsLoading(false)
      }
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
