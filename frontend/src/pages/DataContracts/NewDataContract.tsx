import { useNavigate } from 'react-router-dom'
import { useCreateDataContract } from '../../hooks/useDataContracts'
import PageHeader from '../../components/PageHeader'
import Card from '../../components/ui/Card'
import DataContractForm from './DataContractForm'
import type { DataContractInput } from '../../types'

export default function NewDataContract() {
  const navigate = useNavigate()
  const createMutation = useCreateDataContract()

  const handleSubmit = async (input: DataContractInput) => {
    const created = await createMutation.mutateAsync(input)
    navigate(`/data-contracts/${created.id}`)
  }

  return (
    <div>
      <PageHeader
        title="New Data Contract"
        subtitle="Define a new ODCS-compliant contract for your data product."
        backTo="/data-contracts"
      />
      <Card>
        <DataContractForm
          onSubmit={handleSubmit}
          onCancel={() => navigate('/data-contracts')}
          isSubmitting={createMutation.isPending}
          showWizard
        />
        {createMutation.isError && (
          <p className="mt-3 text-sm text-red-500">{createMutation.error.message}</p>
        )}
      </Card>
    </div>
  )
}
