import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Edit2, Trash2, Calendar, Clock, FileCode } from 'lucide-react'
import {
  useDataContract,
  useUpdateDataContract,
  useDeleteDataContract,
  useDataContractYaml,
} from '../../hooks/useDataContracts'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'
import Badge from '../../components/ui/Badge'
import Modal from '../../components/ui/Modal'
import Spinner from '../../components/ui/Spinner'
import DataContractForm from './DataContractForm'
import type { DataContractInput } from '../../types'

const TIER_COLORS: Record<number, 'red' | 'yellow' | 'blue' | 'gray'> = {
  1: 'red', 2: 'yellow', 3: 'blue', 4: 'gray',
}
const TIER_NAMES: Record<number, string> = {
  1: 'Critical / Regulated', 2: 'Business Important',
  3: 'Operational / Internal', 4: 'Experimental / Sandbox',
}
const STATUS_COLORS: Record<string, 'gray' | 'yellow' | 'green' | 'red'> = {
  draft: 'gray', in_review: 'yellow', active: 'green', deprecated: 'red',
}

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function DataContractDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [editOpen, setEditOpen] = useState(false)
  const [deleteConfirm, setDeleteConfirm] = useState(false)
  const [yamlOpen, setYamlOpen] = useState(false)

  const { data: contract, isLoading, error } = useDataContract(id ?? '')
  const updateMutation = useUpdateDataContract()
  const deleteMutation = useDeleteDataContract()
  const { data: yamlContent, isFetching: yamlLoading } = useDataContractYaml(id ?? '', yamlOpen)

  const handleUpdate = async (input: DataContractInput) => {
    if (!id) return
    await updateMutation.mutateAsync({ id, ...input })
    setEditOpen(false)
  }

  const handleDelete = async () => {
    if (!id) return
    await deleteMutation.mutateAsync(id)
    navigate('/data-contracts')
  }

  const handleApprove = () => {
    if (!id || !contract) return
    updateMutation.mutate({ id, status: 'active' })
  }

  const handleRequestChanges = () => {
    if (!id || !contract) return
    updateMutation.mutate({ id, status: 'draft' })
  }

  if (isLoading) {
    return <div className="flex items-center justify-center h-64"><Spinner size="lg" /></div>
  }

  if (error || !contract) {
    return (
      <div className="text-center py-16">
        <p className="text-red-500 font-medium">{error?.message ?? 'Contract not found'}</p>
        <button onClick={() => navigate('/data-contracts')}
          className="mt-3 text-sm text-blue-600 dark:text-blue-400 hover:underline">
          Back to list
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title={contract.title}
        subtitle={`v${contract.version} · ${contract.domain}`}
        backTo="/data-contracts"
        actions={
          <>
            <Button variant="secondary" size="sm" onClick={() => setYamlOpen(true)}>
              <FileCode size={14} />
              View YAML
            </Button>
            <Button variant="secondary" size="sm" onClick={() => setEditOpen(true)}>
              <Edit2 size={14} />
              Edit
            </Button>
            <Button variant="danger" size="sm" onClick={() => setDeleteConfirm(true)}>
              <Trash2 size={14} />
              Delete
            </Button>
          </>
        }
      />

      {/* Approval actions — only when in_review */}
      {contract.status === 'in_review' && (
        <div className="flex items-center gap-3 p-3 rounded-lg border border-yellow-200 bg-yellow-50 dark:border-yellow-700 dark:bg-yellow-900/20">
          <p className="text-sm text-yellow-800 dark:text-yellow-300 flex-1">
            This contract is awaiting review.
          </p>
          <Button size="sm" onClick={handleApprove} loading={updateMutation.isPending}>
            Approve
          </Button>
          <Button size="sm" variant="secondary" onClick={handleRequestChanges}
            loading={updateMutation.isPending}>
            Request Changes
          </Button>
        </div>
      )}

      {/* Metadata badges */}
      <div className="flex flex-wrap gap-2">
        <Badge variant={TIER_COLORS[contract.tier]}>
          Tier {contract.tier} — {TIER_NAMES[contract.tier]}
        </Badge>
        <Badge variant={STATUS_COLORS[contract.status] ?? 'gray'}>
          {contract.status.replace('_', ' ')}
        </Badge>
        <Badge variant="gray">
          <Calendar size={11} className="mr-1" />
          Created {formatDateTime(contract.created_at)}
        </Badge>
        <Badge variant="gray">
          <Clock size={11} className="mr-1" />
          Updated {formatDateTime(contract.updated_at)}
        </Badge>
      </div>

      {/* Info card */}
      <Card>
        <h2 className="text-sm font-semibold text-gray-700 dark:text-slate-200 mb-3">Info</h2>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
          <div><dt className="text-gray-400 dark:text-slate-500">Owner</dt><dd className="text-gray-800 dark:text-slate-200">{contract.owner}</dd></div>
          <div><dt className="text-gray-400 dark:text-slate-500">Domain</dt><dd className="text-gray-800 dark:text-slate-200">{contract.domain}</dd></div>
          <div><dt className="text-gray-400 dark:text-slate-500">Version</dt><dd className="text-gray-800 dark:text-slate-200">{contract.version}</dd></div>
          <div><dt className="text-gray-400 dark:text-slate-500">Status</dt><dd className="text-gray-800 dark:text-slate-200">{contract.status.replace('_', ' ')}</dd></div>
        </dl>
      </Card>

      {/* Models table */}
      <Card>
        <h2 className="text-sm font-semibold text-gray-700 dark:text-slate-200 mb-3">
          Schema Fields ({contract.models.fields.length})
        </h2>
        {contract.models.fields.length === 0 ? (
          <p className="text-sm text-gray-400 dark:text-slate-500 italic">No fields defined.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-400 dark:text-slate-500 border-b border-gray-200 dark:border-slate-700">
                <th className="pb-2 pr-4">Field</th>
                <th className="pb-2 pr-4">Type</th>
                <th className="pb-2 pr-4">Nullable</th>
                <th className="pb-2 pr-4">PK</th>
                <th className="pb-2">Description</th>
              </tr>
            </thead>
            <tbody>
              {contract.models.fields.map((f, i) => (
                <tr key={i} className="border-b border-gray-100 dark:border-slate-800 last:border-0">
                  <td className="py-2 pr-4 font-mono text-gray-800 dark:text-slate-200">{f.name}</td>
                  <td className="py-2 pr-4 text-gray-600 dark:text-slate-300">{f.type}</td>
                  <td className="py-2 pr-4 text-gray-500 dark:text-slate-400">{f.nullable ? 'yes' : 'no'}</td>
                  <td className="py-2 pr-4 text-gray-500 dark:text-slate-400">{f.primary_key ? '✓' : '—'}</td>
                  <td className="py-2 text-gray-500 dark:text-slate-400">{f.description || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {/* Quality Rules card */}
      {(contract.models.quality ?? []).length > 0 && (
        <Card>
          <h2 className="text-sm font-semibold text-gray-700 dark:text-slate-200 mb-3">
            Quality Rules ({contract.models.quality!.length})
          </h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-gray-400 dark:text-slate-500 border-b border-gray-200 dark:border-slate-700">
                <th className="pb-2 pr-4">Dimension</th>
                <th className="pb-2 pr-4">Column</th>
                <th className="pb-2 pr-4">Operator</th>
                <th className="pb-2 pr-4">Threshold</th>
                <th className="pb-2">Description</th>
              </tr>
            </thead>
            <tbody>
              {contract.models.quality!.map((r, i) => (
                <tr key={i} className="border-b border-gray-100 dark:border-slate-800 last:border-0">
                  <td className="py-2 pr-4 text-gray-800 dark:text-slate-200">{r.dimension}</td>
                  <td className="py-2 pr-4 font-mono text-gray-600 dark:text-slate-300">{r.column || '—'}</td>
                  <td className="py-2 pr-4 text-gray-500 dark:text-slate-400">{r.operator}</td>
                  <td className="py-2 pr-4 text-gray-800 dark:text-slate-200">{r.threshold}</td>
                  <td className="py-2 text-gray-500 dark:text-slate-400">{r.description || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}

      {/* Service Levels card */}
      <Card>
        <h2 className="text-sm font-semibold text-gray-700 dark:text-slate-200 mb-3">Service Levels</h2>
        <dl className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
          <div><dt className="text-gray-400 dark:text-slate-500">Freshness</dt><dd className="text-gray-800 dark:text-slate-200">{contract.servicelevels.freshness || '—'}</dd></div>
          <div><dt className="text-gray-400 dark:text-slate-500">Availability</dt><dd className="text-gray-800 dark:text-slate-200">{contract.servicelevels.availability || '—'}</dd></div>
          <div><dt className="text-gray-400 dark:text-slate-500">Retention</dt><dd className="text-gray-800 dark:text-slate-200">{contract.servicelevels.retention || '—'}</dd></div>
          <div><dt className="text-gray-400 dark:text-slate-500">Latency</dt><dd className="text-gray-800 dark:text-slate-200">{contract.servicelevels.latency || '—'}</dd></div>
        </dl>
      </Card>

      {/* YAML Modal */}
      <Modal open={yamlOpen} onClose={() => setYamlOpen(false)} title="ODCS YAML" size="lg">
        {yamlLoading ? (
          <div className="flex justify-center py-8"><Spinner /></div>
        ) : (
          <pre className="bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-700 rounded-lg p-4 text-xs font-mono text-gray-700 dark:text-slate-300 overflow-x-auto whitespace-pre-wrap">
            {yamlContent}
          </pre>
        )}
      </Modal>

      {/* Edit Modal */}
      <Modal open={editOpen} onClose={() => setEditOpen(false)} title="Edit Data Contract" size="lg">
        <DataContractForm
          defaultValues={contract}
          onSubmit={handleUpdate}
          onCancel={() => setEditOpen(false)}
          isSubmitting={updateMutation.isPending}
        />
        {updateMutation.isError && (
          <p className="mt-3 text-sm text-red-500">{updateMutation.error.message}</p>
        )}
      </Modal>

      {/* Delete Modal */}
      <Modal open={deleteConfirm} onClose={() => setDeleteConfirm(false)} title="Delete Data Contract" size="sm">
        <p className="text-sm text-gray-600 dark:text-slate-300 mb-6">
          Are you sure you want to delete <span className="font-medium">{contract.title}</span>? This cannot be undone.
        </p>
        <div className="flex justify-end gap-3">
          <Button variant="secondary" onClick={() => setDeleteConfirm(false)}>Cancel</Button>
          <Button variant="danger" loading={deleteMutation.isPending} onClick={handleDelete}>Delete</Button>
        </div>
        {deleteMutation.isError && (
          <p className="mt-3 text-sm text-red-500">{deleteMutation.error.message}</p>
        )}
      </Modal>
    </div>
  )
}
