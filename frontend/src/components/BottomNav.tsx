import { NavLink } from 'react-router-dom'
import { LayoutDashboard, FileText, Package, Users, Building2 } from 'lucide-react'

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Home' },
  { to: '/domains', icon: Building2, label: 'Domains' },
  { to: '/data-contracts', icon: FileText, label: 'Contracts' },
  { to: '/data-products', icon: Package, label: 'Products' },
  { to: '/users', icon: Users, label: 'Users' },
]

export default function BottomNav() {
  return (
    <nav aria-label="Mobile navigation" className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-slate-900 border-t border-slate-800 flex items-stretch z-50">
      {navItems.map(({ to, icon: Icon, label }) => (
        <NavLink
          key={to}
          to={to}
          className={({ isActive }) => `bottom-nav-link ${isActive ? 'active' : ''}`}
        >
          <Icon size={20} />
          <span>{label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
