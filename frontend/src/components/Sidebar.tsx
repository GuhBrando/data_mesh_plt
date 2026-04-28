import { useState } from 'react'
import { NavLink, Link } from 'react-router-dom'
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
    <aside className="hidden md:flex w-64 shrink-0 bg-slate-900 min-h-screen flex-col">
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
      <nav aria-label="Main navigation" className="flex-1 p-3 space-y-0.5">
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
        {/* User info — links to profile */}
        {user && (
          <Link
            to="/profile"
            className="flex items-center gap-2 mb-3 px-1 py-1 rounded-lg hover:bg-slate-800 transition-colors group"
            title="View profile"
          >
            <div className="w-6 h-6 rounded-full bg-indigo-600 flex items-center justify-center shrink-0">
              <span className="text-white text-xs font-semibold">
                {user.username.charAt(0).toUpperCase()}
              </span>
            </div>
            <span className="text-slate-300 text-xs truncate group-hover:text-white">
              {user.username}
            </span>
          </Link>
        )}

        <div className="flex items-center justify-between">
          <button
            onClick={handleLogout}
            disabled={isLoggingOut}
            className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-red-900/20 transition-colors text-xs disabled:opacity-50 disabled:cursor-not-allowed"
            title="Sign out"
          >
            <LogOut size={14} />
            {isLoggingOut ? 'Signing out...' : 'Sign out'}
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
