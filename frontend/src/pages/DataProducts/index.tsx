import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, Package, Trash2, Github } from 'lucide-react'
import {
  useDataProducts,
  useCreateDataProduct,
  useDeleteDataProduct,
} from '../../hooks/useDataProducts'
import PageHeader from '../../components/PageHeader'
import Table from '../../components/ui/Table'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import Spinner from '../../components/ui/Spinner'
import DataProductForm from './DataProductForm'
import type { DataProduct, DataProductFormData } from '../../types'

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

export default function DataProductsList() {
  const navigate = useNavigate()
  const [createOpen, setCreateOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<DataProduct | null>(null)

  const { data: products = [], isLoading, error } = useDataProducts()
  const createMutation = useCreateDataProduct()
  const deleteMutation = useDeleteDataProduct()

  const handleCreate = async (values: DataProductFormData) => {
    await createMutation.mutateAsync(values)
    setCreateOpen(false)
  }

  const handleDelete = async () => {
    if (!deleteTarget) return
    await deleteMutation.mutateAsync(deleteTarget.id)
    setDeleteTarget(null)
  }

  const columns = [
    {
      key: 'name',
      header: 'Name',
      render: (row: DataProduct) => (
        <span className="font-medium text-gray-900 dark:text-slate-100">{row.name}</span>
      ),
    },
    {
      key: 'description',
      header: 'Description',
      render: (row: DataProduct) => (
        <span className="text-gray-500 dark:text-slate-400 line-clamp-1">
          {row.description.length > 80
            ? row.description.slice(0, 80) + '…'
            : row.description}
        </span>
      ),
    },
    {
      key: 'contract',
      header: 'Contract ID',
      render: (row: DataProduct) => (
        <span className="font-mono text-xs text-indigo-600 dark:text-indigo-400">
          {truncateId(row.data_contracts_id)}
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Created At',
      render: (row: DataProduct) => (
        <span className="text-sm text-gray-500 dark:text-slate-400">{formatDate(row.created_at)}</span>
      ),
    },
    {
      key: 'github',
      header: '',
      mobileHidden: true,
      render: (row: DataProduct) =>
        row.repo_url ? (
          <a
            href={row.repo_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center justify-center p-1.5 rounded text-gray-500 hover:text-gray-800 hover:bg-gray-100 dark:text-slate-400 dark:hover:text-slate-100 dark:hover:bg-slate-700 transition-colors"
            title="Open GitHub repo"
            aria-label="Open GitHub repo"
          >
            <Github size={13} />
          </a>
        ) : null,
      className: 'w-8',
    },
    {
      key: 'actions',
      header: '',
      render: (row: DataProduct) => (
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
        title="Data Products"
        subtitle={`${products.length} product${products.length !== 1 ? 's' : ''}`}
        actions={
          <Button onClick={() => setCreateOpen(true)}>
            <Plus size={16} />
            New Data Product
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
      ) : products.length === 0 ? (
        <div className="text-center py-20">
          <Package size={48} className="text-gray-200 dark:text-slate-700 mx-auto mb-4" />
          <p className="text-gray-500 dark:text-slate-400 font-medium mb-1">No data products yet</p>
          <p className="text-sm text-gray-400 dark:text-slate-500 mb-4">
            Create your first data product to get started.
          </p>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus size={16} />
            New Data Product
          </Button>
        </div>
      ) : (
        <Table
          columns={columns}
          data={products}
          keyExtractor={(p) => p.id}
          onRowClick={(p) => navigate(`/data-products/${p.id}`)}
          emptyMessage="No products found."
          mobileCardConfig={{ titleKey: 'name' }}
        />
      )}

      {/* Create Modal */}
      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="New Data Product"
      >
        <DataProductForm
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
        title="Delete Data Product"
        size="sm"
      >
        <p className="text-sm text-gray-600 dark:text-slate-300 mb-2">
          Are you sure you want to delete{' '}
          <span className="font-medium">{deleteTarget?.name}</span>?
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
