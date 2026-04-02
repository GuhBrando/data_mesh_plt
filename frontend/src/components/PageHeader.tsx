import { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft } from 'lucide-react'

interface PageHeaderProps {
  title: string
  subtitle?: string
  actions?: ReactNode
  backTo?: string
}

export default function PageHeader({
  title,
  subtitle,
  actions,
  backTo,
}: PageHeaderProps) {
  const navigate = useNavigate()

  return (
    <div className="flex items-start justify-between mb-6">
      <div className="flex items-start gap-3">
        {backTo && (
          <button
            onClick={() => navigate(backTo)}
            className="mt-0.5 p-1.5 rounded-lg text-gray-400 hover:text-gray-700 hover:bg-gray-100 transition-colors dark:text-slate-500 dark:hover:text-slate-200 dark:hover:bg-slate-700"
            aria-label="Go back"
          >
            <ChevronLeft size={18} />
          </button>
        )}
        <div>
          <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100">{title}</h1>
          {subtitle && (
            <p className="mt-0.5 text-sm text-gray-500 dark:text-slate-400">{subtitle}</p>
          )}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}
