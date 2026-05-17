import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Database, Sun, Moon, LogOut } from 'lucide-react'
import { useTheme } from '../contexts/ThemeContext'
import { useAuth } from '../contexts/AuthContext'
import { post } from '../lib/api'
import { getRefreshToken } from '../lib/auth'

export default function MobileHeader() {
  const { theme, toggle } = useTheme()
  const { user, logout } = useAuth()
  const [isLoggingOut, setIsLoggingOut] = useState(false)

  async function handleLogout() {
    setIsLoggingOut(true)
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
    <header className="md:hidden sticky top-0 z-40 flex items-center justify-between px-4 py-3 bg-slate-900 border-b border-slate-800 shrink-0">
      {/* Brand */}
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center shrink-0">
          <Database size={14} className="text-white" />
        </div>
        <span className="text-white font-semibold text-sm">Data Mesh</span>
      </div>

      {/* Right side: user + theme + logout */}
      <div className="flex items-center gap-1">
        {user && (
          <Link
            to="/profile"
            className="flex items-center gap-1.5 mr-1 py-1 px-1 rounded-lg hover:bg-slate-800 transition-colors"
            title="View profile"
          >
            <div className="w-6 h-6 rounded-full bg-indigo-600 flex items-center justify-center shrink-0">
              <span className="text-white text-xs font-semibold">
                {user.username.charAt(0).toUpperCase()}
              </span>
            </div>
            <span className="text-slate-300 text-xs max-w-[80px] truncate">{user.username}</span>
          </Link>
        )}

        <button
          onClick={toggle}
          className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-700 transition-colors"
          aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
        </button>

        <button
          onClick={handleLogout}
          disabled={isLoggingOut}
          className="flex items-center gap-1 px-2 py-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-900/20 transition-colors text-xs disabled:opacity-50 disabled:cursor-not-allowed"
          title="Sign out"
        >
          <LogOut size={14} />
          {isLoggingOut ? 'Signing out…' : 'Sign out'}
        </button>
      </div>
    </header>
  )
}
