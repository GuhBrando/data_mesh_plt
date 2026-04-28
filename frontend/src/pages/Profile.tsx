import { Shield, Building2, User as UserIcon, ChevronRight } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { useUserDomains } from '../hooks/useProfile'

const ROLE_META: Record<
  string,
  { label: string; color: string; description: string; permissions: string[] }
> = {
  PLATFORM_ADMIN: {
    label: 'Platform Admin',
    color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
    description: 'Full control over all platform resources.',
    permissions: [
      'Create and delete users',
      'Assign any role to any user',
      'Create domains and manage all domain memberships',
      'Create, edit, and delete any data contract',
      'Assign stakeholders to any contract',
    ],
  },
  DATA_OWNER: {
    label: 'Data Owner',
    color: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
    description: 'Governs your domain and its data contracts.',
    permissions: [
      'Add and remove members within your domain',
      'Approve, reject, and delete contracts in your domain',
      'View all data contracts',
    ],
  },
  DATA_STEWARD: {
    label: 'Data Steward',
    color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
    description: 'Creates and manages data contracts in your domain.',
    permissions: [
      'Create and edit data contracts within your domain',
      'Assign stakeholders to contracts in your domain',
      'View all data contracts',
    ],
  },
  DATA_CONSUMER: {
    label: 'Data Consumer',
    color: 'bg-slate-100 text-slate-700 dark:bg-slate-700/50 dark:text-slate-300',
    description: 'Read-only access to contracts where you are a stakeholder.',
    permissions: [
      'View data contracts where assigned as stakeholder',
      'View your own profile and domain memberships',
    ],
  },
}

export default function Profile() {
  const { user } = useAuth()
  const { data: domains, isLoading: domainsLoading } = useUserDomains(user?.id)

  if (!user) return null

  const role = ROLE_META[user.role] ?? {
    label: user.role,
    color: 'bg-slate-100 text-slate-700 dark:bg-slate-700/50 dark:text-slate-300',
    description: '',
    permissions: [],
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-slate-900 dark:text-white">My Profile</h1>

      {/* Identity card */}
      <div className="card p-6 flex items-center gap-5">
        <div className="w-14 h-14 rounded-full bg-indigo-600 flex items-center justify-center shrink-0">
          <span className="text-white text-2xl font-bold">
            {user.username.charAt(0).toUpperCase()}
          </span>
        </div>
        <div className="min-w-0">
          <p className="text-lg font-semibold text-slate-900 dark:text-white truncate">
            {user.username}
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-400 truncate">{user.email}</p>
          <span
            className={`mt-1.5 inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${role.color}`}
          >
            {role.label}
          </span>
        </div>
      </div>

      {/* Permissions card */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Shield size={16} className="text-slate-500 dark:text-slate-400 shrink-0" />
          <h2 className="font-semibold text-slate-900 dark:text-white">Permissions</h2>
        </div>

        {role.description && (
          <p className="text-sm text-slate-600 dark:text-slate-400">{role.description}</p>
        )}

        <ul className="space-y-2">
          {role.permissions.map((p) => (
            <li key={p} className="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-300">
              <ChevronRight
                size={14}
                className="mt-0.5 shrink-0 text-blue-500 dark:text-blue-400"
              />
              {p}
            </li>
          ))}
        </ul>
      </div>

      {/* Domains card */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center gap-2">
          <Building2 size={16} className="text-slate-500 dark:text-slate-400 shrink-0" />
          <h2 className="font-semibold text-slate-900 dark:text-white">Domain Memberships</h2>
        </div>

        {domainsLoading ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>
        ) : domains && domains.length > 0 ? (
          <ul className="divide-y divide-slate-100 dark:divide-slate-700">
            {domains.map((d) => (
              <li key={d.id} className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0">
                <div className="w-7 h-7 rounded-md bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center shrink-0">
                  <UserIcon size={13} className="text-blue-600 dark:text-blue-400" />
                </div>
                <span className="text-sm text-slate-800 dark:text-slate-200 font-medium">
                  {d.name}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            You are not a member of any domain yet.
          </p>
        )}
      </div>
    </div>
  )
}
