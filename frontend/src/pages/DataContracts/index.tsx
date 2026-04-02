import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, FileText, Trash2 } from 'lucide-react'
import {
  useDataContracts,
  useCreateDataContract,
  useDeleteDataContract,
} from '../../hooks/useDataContracts'
import PageHeader from '../../components/PageHeader'
import Table from '../../components/ui/Table'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Spinner from '../../components/ui/Spinner'
import DataContractForm from './DataContractForm'
import type { DataContract } from '../../types'

function truncateId(id: string) {
  return id.slice(0, 8) + '…'
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export default function DataContractsList() {
  const navigate = useNavigate()
  const [createOpen, setCreateOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<DataContract | null>(null)

  const { data: contracts = [], isLoading, error } = useDataContracts()
  const createMutation = useCreateDataContract()
  const deleteMutation = useDeleteDataContract()

  const handleCreate = async (obj: Record<string, unknown>) => {
    await createMutation.mutateAsync(obj)
    setCreateOpen(false)
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    await deleteMutation.mutateAsync(deleteTarget.id)
    setDeleteTarget(null)
  }

  const columns = [
    {
      key: 'id',
      header: 'ID',
      render: (row: DataContract) => (
        <span className="font-mono text-xs text-gray-500 dark:text-slate-400">
          {truncateId(row.id)}
        </span>
      ),
    },
    {
      key: 'preview',
      header: 'Contract Preview',
      render: (row: DataContract) => {
        const keys = Object.keys(row.obj)
        if (keys.length === 0) return <span className="text-gray-400 dark:text-slate-500 italic">empty</span>
        const firstKey = keys[0]
        const firstVal = row.obj[firstKey]
        return (
          <span className="text-sm text-gray-700 dark:text-slate-300">
            <span className="font-medium text-gray-500 dark:text-slate-400">{firstKey}:</span>{' '}
            {String(firstVal).slice(0, 60)}
            {keys.length > 1 && (
              <span className="ml-1 text-xs text-gray-400 dark:text-slate-500">
                +{keys.length - 1} more
              </span>
            )}
          </span>
        )
      },
    },
    {
      key: 'created_at',
      header: 'Created At',
      render: (row: DataContract) => (
        <span className="text-sm text-gray-500 dark:text-slate-400">{formatDate(row.created_at)}</span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (row: DataContract) => (
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
      ),
      className: 'w-24',
    },
  ]

  return (
    <div>
      <PageHeader
        title="Data Contracts"
        subtitle={`${contracts.length} contract${contracts.length !== 1 ? 's' : ''}`}
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus size={16} />
            New Contract
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
      ) : contracts.length === 0 ? (
        <div className="text-center py-20">
          <FileText size={48} className="text-gray-200 dark:text-slate-700 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-slate-400 font-medium mb-1">No data contracts yet</p>
          <p className="text-sm text-gray-400 dark:text-slate-500 mb-4">
            Create your first contract to get started.
          </p>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus size={16} />
            New Contract
          </Button>
        </div>
      ) : (
        <Table
          columns={columns}
          data={contracts}
          keyExtractor={(c) => c.id}
          onRowClick={(c) => navigate(`/data-contracts/${c.id}`)}
          emptyMessage="No contracts found."
        />
      )}

      {/* Create Modal */}
      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="New Data Contract"
        size="lg"
      >
        <DataContractForm
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

      {/* Delete Confirmation Modal */}
      <Modal
        open={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        title="Delete Data Contract"
        size="sm"
      >
        <p className="text-sm text-gray-600 dark:text-slate-300 mb-2">
          Are you sure you want to delete contract{' '}
          <span className="font-mono font-medium">
            {deleteTarget ? truncateId(deleteTarget.id) : ''}
          </span>
          ?
        </p>
        <p className="text-xs text-gray-400 dark:text-slate-500 mb-6">This action cannot be undone.</p>
        <div className="flex justify-end gap-3">
          <Button
            variant="secondary"
            onClick={() => setDeleteTarget(null)}
          >
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
