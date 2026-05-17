import { type ElementType } from 'react'
import { useNavigate } from 'react-router-dom'
import { Package, FileText, Users, TrendingUp, ArrowRight } from 'lucide-react'
import { useDataContracts } from '../hooks/useDataContracts'
import { useDataProducts } from '../hooks/useDataProducts'
import { useUsers } from '../hooks/useUsers'
import Card from '../components/ui/Card'
import Badge from '../components/ui/Badge'
import Spinner from '../components/ui/Spinner'

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function StatCard({
  label,
  value,
  icon: Icon,
  color,
  loading,
}: {
  label: string
  value: number
  icon: ElementType
  color: string
  loading: boolean
}) {
  return (
    <Card className="flex items-center gap-4">
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${color}`}>
        <Icon size={22} className="text-white" />
      </div>
      <div>
        {loading ? (
          <Spinner size="sm" />
        ) : (
          <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">{value}</p>
        )}
        <p className="text-sm text-gray-500 dark:text-slate-400">{label}</p>
      </div>
    </Card>
  )
}

export default function Dashboard() {
  const navigate = useNavigate()
  const { data: products = [], isLoading: loadingProducts } = useDataProducts()
  const { data: contracts = [], isLoading: loadingContracts } = useDataContracts()
  const { data: users = [], isLoading: loadingUsers } = useUsers()

  const recentProducts = [...products]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)

  const recentContracts = [...contracts]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)

  return (
    <div>
      <div className="mb-8">
        <div className="flex items-center gap-2 mb-1">
          <TrendingUp size={20} className="text-blue-600" />
          <h1 className="text-xl font-bold text-gray-900 dark:text-slate-100">Dashboard</h1>
        </div>
        <p className="text-sm text-gray-500 dark:text-slate-400">
          Overview of your data mesh platform resources.
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <StatCard
          label="Data Products"
          value={products.length}
          icon={Package}
          color="bg-blue-500"
          loading={loadingProducts}
        />
        <StatCard
          label="Data Contracts"
          value={contracts.length}
          icon={FileText}
          color="bg-indigo-500"
          loading={loadingContracts}
        />
        <StatCard
          label="Users"
          value={users.length}
          icon={Users}
          color="bg-violet-500"
          loading={loadingUsers}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Data Products */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Package size={16} className="text-blue-600" />
              <h2 className="text-sm font-semibold text-gray-900 dark:text-slate-100">
                Recent Data Products
              </h2>
            </div>
            <button
              onClick={() => navigate('/data-products')}
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
            >
              View all <ArrowRight size={12} />
            </button>
          </div>

          {loadingProducts ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : recentProducts.length === 0 ? (
            <div className="text-center py-8">
              <Package size={32} className="text-gray-200 dark:text-slate-700 mx-auto mb-2" />
              <p className="text-sm text-gray-400 dark:text-slate-500">No data products yet.</p>
              <button
                onClick={() => navigate('/data-products')}
                className="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                Create one
              </button>
            </div>
          ) : (
            <ul className="space-y-2">
              {recentProducts.map((p) => (
                <li
                  key={p.id}
                  onClick={() => navigate(`/data-products/${p.id}`)}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700 cursor-pointer group transition-colors"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-800 dark:text-slate-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 truncate">
                      {p.name}
                    </p>
                    <p className="text-xs text-gray-400 dark:text-slate-500 truncate">{p.description}</p>
                  </div>
                  <Badge variant="blue" className="ml-2 shrink-0">
                    {formatDate(p.created_at)}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </Card>

        {/* Recent Data Contracts */}
        <Card>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <FileText size={16} className="text-indigo-600" />
              <h2 className="text-sm font-semibold text-gray-900 dark:text-slate-100">
                Recent Data Contracts
              </h2>
            </div>
            <button
              onClick={() => navigate('/data-contracts')}
              className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium"
            >
              View all <ArrowRight size={12} />
            </button>
          </div>

          {loadingContracts ? (
            <div className="flex justify-center py-8">
              <Spinner />
            </div>
          ) : recentContracts.length === 0 ? (
            <div className="text-center py-8">
              <FileText size={32} className="text-gray-200 dark:text-slate-700 mx-auto mb-2" />
              <p className="text-sm text-gray-400 dark:text-slate-500">No data contracts yet.</p>
              <button
                onClick={() => navigate('/data-contracts')}
                className="mt-2 text-xs text-blue-600 dark:text-blue-400 hover:underline"
              >
                Create one
              </button>
            </div>
          ) : (
            <ul className="space-y-2">
              {recentContracts.map((c) => (
                  <li
                    key={c.id}
                    onClick={() => navigate(`/data-contracts/${c.id}`)}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 dark:hover:bg-slate-700 cursor-pointer group transition-colors"
                  >
                    <div className="min-w-0">
                      <p className="text-xs font-mono text-gray-500 dark:text-slate-400 truncate">
                        {c.domain}
                      </p>
                      <p className="text-sm font-medium text-gray-800 dark:text-slate-200 group-hover:text-blue-600 dark:group-hover:text-blue-400 truncate">
                        {c.title}
                      </p>
                    </div>
                    <Badge variant="purple" className="ml-2 shrink-0">
                      {formatDate(c.created_at)}
                    </Badge>
                  </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  )
}
