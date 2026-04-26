import { useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Button from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import TierWizard from './TierWizard'
import ContractFields from './ContractFields'
import type { DataContract, DataContractInput, SchemaField } from '../../types'

const schema = z.object({
  title: z.string().min(1, 'Title is required'),
  version: z.string().min(1, 'Version is required'),
  owner: z.string().min(1, 'Owner is required'),
  domain: z.string().min(1, 'Domain is required'),
  tier: z.number().int().min(1).max(4),
  status: z.enum(['draft', 'in_review', 'active', 'deprecated']),
  freshness: z.string(),
  availability: z.string(),
  retention: z.string(),
  latency: z.string(),
})

type FormValues = z.infer<typeof schema>

interface DataContractFormProps {
  defaultValues?: DataContract
  onSubmit: (input: DataContractInput) => void
  onCancel: () => void
  isSubmitting: boolean
  showWizard?: boolean
}

export default function DataContractForm({
  defaultValues,
  onSubmit,
  onCancel,
  isSubmitting,
  showWizard = false,
}: DataContractFormProps) {
  const [fields, setFields] = useState<SchemaField[]>(
    defaultValues?.models?.fields ?? []
  )

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      title: defaultValues?.title ?? '',
      version: defaultValues?.version ?? '1.0.0',
      owner: defaultValues?.owner ?? '',
      domain: defaultValues?.domain ?? '',
      tier: defaultValues?.tier ?? 4,
      status: defaultValues?.status ?? 'draft',
      freshness: defaultValues?.servicelevels?.freshness ?? '',
      availability: defaultValues?.servicelevels?.availability ?? '',
      retention: defaultValues?.servicelevels?.retention ?? '',
      latency: defaultValues?.servicelevels?.latency ?? '',
    },
  })

  const handleFormSubmit = (values: FormValues) => {
    onSubmit({
      title: values.title,
      version: values.version,
      owner: values.owner,
      domain: values.domain,
      tier: values.tier,
      status: values.status,
      models: { fields },
      servicelevels: {
        freshness: values.freshness,
        availability: values.availability,
        retention: values.retention,
        latency: values.latency,
      },
    })
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Step 1 — Tier Wizard (only on creation page) */}
      {showWizard && (
        <Controller
          name="tier"
          control={control}
          render={({ field }) => (
            <TierWizard value={field.value} onChange={field.onChange} />
          )}
        />
      )}

      {/* Step 2 — Contract Info */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-200">
          {showWizard ? 'Step 2 — Contract Info' : 'Contract Info'}
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <Input
            label="Title"
            error={errors.title?.message}
            {...register('title')}
          />
          <Input
            label="Version"
            error={errors.version?.message}
            {...register('version')}
          />
          <Input
            label="Owner"
            error={errors.owner?.message}
            {...register('owner')}
          />
          <Input
            label="Domain"
            error={errors.domain?.message}
            {...register('domain')}
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          {!showWizard && (
            <div>
              <label className="block text-xs font-medium text-gray-600 dark:text-slate-400 mb-1">
                Tier
              </label>
              <select
                className="w-full text-sm border border-gray-300 dark:border-slate-600 rounded-lg px-3 py-2 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
                {...register('tier', { valueAsNumber: true })}
              >
                <option value={1}>Tier 1 — Critical / Regulated</option>
                <option value={2}>Tier 2 — Business Important</option>
                <option value={3}>Tier 3 — Operational / Internal</option>
                <option value={4}>Tier 4 — Experimental / Sandbox</option>
              </select>
            </div>
          )}
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-slate-400 mb-1">
              Status
            </label>
            <select
              className="w-full text-sm border border-gray-300 dark:border-slate-600 rounded-lg px-3 py-2 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
              {...register('status')}
            >
              <option value="draft">Draft</option>
              <option value="in_review">In Review</option>
              <option value="active">Active</option>
              <option value="deprecated">Deprecated</option>
            </select>
          </div>
        </div>
      </div>

      {/* Step 3 — Models */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-200">
          {showWizard ? 'Step 3 — Schema Fields' : 'Schema Fields'}
        </h3>
        <ContractFields fields={fields} onChange={setFields} />
      </div>

      {/* Step 4 — Service Levels */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-200">
          {showWizard ? 'Step 4 — Service Levels' : 'Service Levels'}
        </h3>
        <div className="grid grid-cols-2 gap-3">
          <Input label="Freshness" placeholder="e.g. 24h" {...register('freshness')} />
          <Input label="Availability" placeholder="e.g. 99.9%" {...register('availability')} />
          <Input label="Retention" placeholder="e.g. 365d" {...register('retention')} />
          <Input label="Latency" placeholder="e.g. 1h" {...register('latency')} />
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-2 border-t border-gray-200 dark:border-slate-700">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={isSubmitting}>
          {defaultValues ? 'Save Changes' : 'Create Contract'}
        </Button>
      </div>
    </form>
  )
}
