import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Edit2, Trash2, Calendar, Clock } from 'lucide-react'
import {
  useDataContract,
  useUpdateDataContract,
  useDeleteDataContract,
} from '../../hooks/useDataContracts'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import Modal from '../../components/ui/Modal'
import Spinner from '../../components/ui/Spinner'
import DataContractForm from './DataContractForm'

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function DataContractDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [editOpen, setEditOpen] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(false)

  const { data: contract, isLoading, error } = useDataContract(id ?? '')
  const updateMutation = useUpdateDataContract()
  const deleteMutation = useDeleteDataContract()

  const handleUpdate = async (obj: Record<string, unknown>) => {
    if (!id) return
    await updateMutation.mutateAsync({ id, obj })
    setEditOpen(false)
  }

  const handleDelete = async () => {
    if (!id) return
    await deleteMutation.mutateAsync(id)
    navigate('/data-contracts')
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner size="lg" />
      </div>
    )
  }

  if (error || !contract) {
    return (
      <div className="text-center py-16">
        <p className="text-red-500 font-medium">
          {error?.message ?? 'Contract not found'}
        </p>
        <button
          onClick={() => navigate('/data-contracts')}
          className="mt-3 text-sm text-blue-600 dark:text-blue-400 hover:underline"
        >
          Back to list
        </button>
      </div>
    )
  }

  return (
    <div>
      <PageHeader
        title="Data Contract Detail"
        subtitle={contract.id}
        backTo="/data-contracts"
        actions={
          <>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setEditOpen(true)}
            >
              <Edit2 size={14} />
              Edit
            </Button>
            <Button
              variant="danger"
              size="sm"
              onClick={() => setDeleteConfirm(true)}
            >
              <Trash2 size={14} />
              Delete
            </Button>
          </>
        }
      />

      {/* Metadata row */}
      <div className="flex flex-wrap gap-3 mb-6">
        <Badge variant="gray">
          <Calendar size={11} className="mr-1" />
          Created {formatDateTime(contract.created_at)}
        </Badge>
        <Badge variant="gray">
          <Clock size={11} className="mr-1" />
          Updated {formatDateTime(contract.updated_at)}
        </Badge>
      </div>

      {/* Contract object */}
      <Card>
        <h2 className="text-sm font-semibold text-gray-700 dark:text-slate-200 mb-3">
          Contract Object
        </h2>
        <pre className="bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-lg p-4 text-xs font-mono text-gray-700 dark:text-slate-300 overflow-x-auto whitespace-pre-wrap break-words">
          {JSON.stringify(contract.obj, null, 2)}
        </pre>
      </Card>

      {/* Edit Modal */}
      <Modal
        open={editOpen}
        onClose={() => setEditOpen(false)}
        title="Edit Data Contract"
        size="lg"
      >
        <DataContractForm
          defaultValues={contract}
          onSubmit={handleUpdate}
          onCancel={() => setEditOpen(false)}
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
        open={deleteConfirm}
        onClose={() => setDeleteConfirm(false)}
        title="Delete Data Contract"
        size="sm"
      >
        <p className="text-sm text-gray-600 dark:text-slate-300 mb-6">
          Are you sure you want to delete this contract? This action cannot be
          undone.
        </p>
        <div className="flex justify-end gap-3">
          <Button
            variant="secondary"
            onClick={() => setDeleteConfirm(false)}
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
