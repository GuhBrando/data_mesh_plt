import { useState } from 'react'
import { Plus, Users as UsersIcon, Trash2, Edit2 } from 'lucide-react'
import {
  useUsers,
  useCreateUser,
  useUpdateUser,
  useDeleteUser,
} from '../../hooks/useUsers'
import PageHeader from '../../components/PageHeader'
import Table from '../../components/ui/Table'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Badge from '../../components/ui/Badge'
import Spinner from '../../components/ui/Spinner'
import UserForm from './UserForm'
import type { User, UserFormData } from '../../types'

export default function UsersList() {
  const [createOpen, setCreateOpen] = useState(false)
  const [editTarget, setEditTarget] = useState<User | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null)

  const { data: users = [], isLoading, error } = useUsers()
  const createMutation = useCreateUser()
  const updateMutation = useUpdateUser()
  const deleteMutation = useDeleteUser()

  const handleCreate = async (values: UserFormData) => {
    await createMutation.mutateAsync(values)
    setCreateOpen(false)
  }

  const handleUpdate = async (values: UserFormData) => {
    if (!editTarget) return
    await updateMutation.mutateAsync({ id: editTarget.id, ...values })
    setEditTarget(null)
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    await deleteMutation.mutateAsync(deleteTarget.id)
    setDeleteTarget(null)
  }

  // Generate initials avatar color from name
  function avatarColor(name: string): string {
    const colors = [
      'bg-blue-500',
      'bg-indigo-500',
      'bg-violet-500',
      'bg-green-500',
      'bg-amber-500',
      'bg-rose-500',
      'bg-teal-500',
    ]
    const idx = name.charCodeAt(0) % colors.length
    return colors[idx]
  }

  function initials(name: string) {
    return name
      .split(' ')
      .map((n) => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase()
  }

  const columns = [
    {
      key: 'name',
      header: 'Name',
      render: (row: User) => (
        <div className="flex items-center gap-3">
          <div
            className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-semibold shrink-0 ${avatarColor(row.username)}`}
          >
            {initials(row.username)}
          </div>
          <span className="font-medium text-gray-900 dark:text-slate-100">{row.username}</span>
        </div>
      ),
    },
    {
      key: 'email',
      header: 'Email',
      render: (row: User) => (
        <a
          href={`mailto:${row.email}`}
          className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          {row.email}
        </a>
      ),
    },
    {
      key: 'id',
      header: 'ID',
      render: (row: User) => (
        <Badge variant="gray">
          <span className="font-mono">{row.id.slice(0, 8)}…</span>
        </Badge>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (row: User) => (
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              setEditTarget(row)
            }}
            className="p-1.5 rounded-lg text-gray-400 hover:text-blue-600 hover:bg-blue-50 transition-colors dark:text-slate-500 dark:hover:text-blue-400 dark:hover:bg-blue-900/20"
            title="Edit"
          >
            <Edit2 size={14} />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              setDeleteTarget(row)
            }}
            className="btn-danger"
            title="Delete"
          >
            <Trash2 size={13} />
            Delete
          </button>
        </div>
      ),
      className: 'w-32',
    },
  ]

  return (
    <div>
      <PageHeader
        title="Users"
        subtitle={`${users.length} user${users.length !== 1 ? 's' : ''}`}
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus size={16} />
            New User
          </Button>
        }
      />

      {isLoading ? (
        <div className="flex justify-center py-20">
          <Spinner size="lg" />
        </div>
      ) : error ? (
        <div className="text-center py-16">
          <p className="text-red-500">{error.message}</p>
        </div>
      ) : users.length === 0 ? (
        <div className="text-center py-20">
          <UsersIcon size={48} className="text-gray-200 dark:text-slate-700 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-slate-400 font-medium mb-1">No users yet</p>
          <p className="text-sm text-gray-400 dark:text-slate-500 mb-4">
            Add your first user to get started.
          </p>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus size={16} />
            New User
          </Button>
        </div>
      ) : (
        <Table
          columns={columns}
          data={users}
          keyExtractor={(u) => u.id}
          emptyMessage="No users found."
        />
      )}

      {/* Create Modal */}
      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="New User"
        size="sm"
      >
        <UserForm
          onSubmit={handleCreate}
          onCancel={() => setCreateOpen(false)}
          isSubmitting={createMutation.isPending}
        />
        {createMutation.isError && (
          <p className="mt-3 text-sm text-red-500">
            {createMutation.error.message}
          </p>
        )}
      </Modal>

      {/* Edit Modal */}
      <Modal
        open={!!editTarget}
        onClose={() => setEditTarget(null)}
        title="Edit User"
        size="sm"
      >
        <UserForm
          defaultValues={editTarget ?? undefined}
          onSubmit={handleUpdate}
          onCancel={() => setEditTarget(null)}
          isSubmitting={updateMutation.isPending}
        />
        {updateMutation.isError && (
          <p className="mt-3 text-sm text-red-500">
            {updateMutation.error.message}
          </p>
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete User"
        size="sm"
      >
        <p className="text-sm text-gray-600 dark:text-slate-300 mb-2">
          Are you sure you want to delete{' '}
          <span className="font-medium">{deleteTarget?.username}</span>?
        </p>
        <p className="text-xs text-gray-400 dark:text-slate-500 mb-6">This action cannot be undone.</p>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={() => setDeleteTarget(null)}>
            Cancel
          </Button>
          <Button
            variant="danger"
            loading={deleteMutation.isPending}
            onClick={handleDelete}
            className="btn-primary bg-red-600 hover:bg-red-700 focus:ring-red-500"
          >
            Delete
          </Button>
        </div>
        {deleteMutation.isError && (
          <p className="mt-3 text-sm text-red-500">
            {deleteMutation.error.message}
          </p>
        )}
      </Modal>
    </div>
  )
}
