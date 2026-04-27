import { useState } from 'react'
import { useForm, Controller } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Button from '../../components/ui/Button'
import { Input } from '../../components/ui/Input'
import TierWizard from './TierWizard'
import ContractFields from './ContractFields'
import QualityRules from './QualityRules'
import type { DataContract, DataContractInput, SchemaField, QualityRule } from '../../types'

const tierRequiresAllSLAs = (t: number) => t === 1
const tierRequiresFreshnessAvailability = (t: number) => t === 2
const tierShowsSLAs = (t: number) => t <= 3
const tierShowsQuality = (t: number) => t <= 3
const tierRequiresQuality = (t: number) => t === 1
const tierRequiresFields = (t: number) => t <= 2

const schema = z
  .object({
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
  .superRefine((data, ctx) => {
    if (data.tier === 1) {
      if (!data.freshness) ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Required for Tier 1', path: ['freshness'] })
      if (!data.availability) ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Required for Tier 1', path: ['availability'] })
      if (!data.retention) ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Required for Tier 1', path: ['retention'] })
      if (!data.latency) ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Required for Tier 1', path: ['latency'] })
    }
    if (data.tier === 2) {
      if (!data.freshness) ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Required for Tier 2', path: ['freshness'] })
      if (!data.availability) ctx.addIssue({ code: z.ZodIssueCode.custom, message: 'Required for Tier 2', path: ['availability'] })
    }
  })

type FormValues = z.infer<typeof schema>

interface DataContractFormProps {
  defaultValues?: DataContract
  onSubmit: (input: DataContractInput) => void
  onCancel: () => void
  isSubmitting: boolean
  showWizard?: boolean
}

function SectionHeader({
  label,
  required,
  optional,
}: {
  label: string
  required?: boolean
  optional?: boolean
}) {
  return (
    <div className="flex items-center gap-2">
      <h3 className="text-sm font-semibold text-gray-700 dark:text-slate-200">{label}</h3>
      {required && (
        <span className="text-xs px-1.5 py-0.5 bg-red-50 text-red-600 border border-red-200 rounded dark:bg-red-900/20 dark:text-red-400 dark:border-red-800">
          Required
        </span>
      )}
      {optional && (
        <span className="text-xs px-1.5 py-0.5 bg-gray-100 text-gray-500 border border-gray-200 rounded dark:bg-slate-700 dark:text-slate-400 dark:border-slate-600">
          Optional
        </span>
      )}
    </div>
  )
}

export default function DataContractForm({
  defaultValues,
  onSubmit,
  onCancel,
  isSubmitting,
  showWizard = false,
}: DataContractFormProps) {
  const [tierDone, setTierDone] = useState(!showWizard)
  const [fields, setFields] = useState<SchemaField[]>(defaultValues?.models?.fields ?? [])
  const [quality, setQuality] = useState<QualityRule[]>(defaultValues?.models?.quality ?? [])
  const [fieldsError, setFieldsError] = useState<string | null>(null)
  const [qualityError, setQualityError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    control,
    watch,
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

  const tier = watch('tier')

  const handleFormSubmit = (values: FormValues) => {
    let valid = true

    if (tierRequiresFields(values.tier) && fields.length === 0) {
      setFieldsError(`At least one schema field is required for Tier ${values.tier}`)
      valid = false
    } else {
      setFieldsError(null)
    }

    if (tierRequiresQuality(values.tier) && quality.length === 0) {
      setQualityError('At least one quality rule is required for Tier 1')
      valid = false
    } else {
      setQualityError(null)
    }

    if (!valid) return

    onSubmit({
      title: values.title,
      version: values.version,
      owner: values.owner,
      domain: values.domain,
      tier: values.tier,
      status: values.status,
      models: {
        fields,
        quality: tierShowsQuality(values.tier) ? quality : [],
      },
      servicelevels: tierShowsSLAs(values.tier)
        ? {
            freshness: values.freshness,
            availability: values.availability,
            retention: values.retention,
            latency: values.latency,
          }
        : { freshness: '', availability: '', retention: '', latency: '' },
    })
  }

  const stepPrefix = (n: number) => (showWizard ? `Step ${n} — ` : '')

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-6">
      {/* Step 1 — Tier Wizard (creation only) */}
      {showWizard && (
        <Controller
          name="tier"
          control={control}
          render={({ field }) => (
            <TierWizard
              value={field.value}
              onChange={(t) => {
                field.onChange(t)
                setTierDone(true)
              }}
            />
          )}
        />
      )}

      {/* Rest of form — revealed after tier is assigned */}
      {tierDone && (
        <>
          {/* Contract Info */}
          <div className="space-y-3">
            <SectionHeader label={`${stepPrefix(2)}Contract Info`} />
            <div className="grid grid-cols-2 gap-3">
              <Input label="Title" error={errors.title?.message} {...register('title')} />
              <Input label="Version" error={errors.version?.message} {...register('version')} />
              <Input label="Owner" error={errors.owner?.message} {...register('owner')} />
              <Input label="Domain" error={errors.domain?.message} {...register('domain')} />
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

          {/* Schema Fields */}
          <div className="space-y-3">
            <SectionHeader
              label={`${stepPrefix(3)}Schema Fields`}
              required={tierRequiresFields(tier)}
              optional={!tierRequiresFields(tier)}
            />
            <ContractFields fields={fields} onChange={setFields} />
            {fieldsError && <p className="text-xs text-red-500 mt-1">{fieldsError}</p>}
          </div>

          {/* Service Levels — hidden for Tier 4 */}
          {tierShowsSLAs(tier) && (
            <div className="space-y-3">
              <SectionHeader
                label={`${stepPrefix(4)}Service Levels`}
                required={tierRequiresAllSLAs(tier) || tierRequiresFreshnessAvailability(tier)}
                optional={!tierRequiresAllSLAs(tier) && !tierRequiresFreshnessAvailability(tier)}
              />
              <div className="grid grid-cols-2 gap-3">
                <Input
                  label={`Freshness${tierRequiresAllSLAs(tier) || tierRequiresFreshnessAvailability(tier) ? ' *' : ''}`}
                  placeholder="e.g. 24h"
                  error={errors.freshness?.message}
                  {...register('freshness')}
                />
                <Input
                  label={`Availability${tierRequiresAllSLAs(tier) || tierRequiresFreshnessAvailability(tier) ? ' *' : ''}`}
                  placeholder="e.g. 99.9%"
                  error={errors.availability?.message}
                  {...register('availability')}
                />
                <Input
                  label={`Retention${tierRequiresAllSLAs(tier) ? ' *' : ''}`}
                  placeholder="e.g. 365d"
                  error={errors.retention?.message}
                  {...register('retention')}
                />
                <Input
                  label={`Latency${tierRequiresAllSLAs(tier) ? ' *' : ''}`}
                  placeholder="e.g. 1h"
                  error={errors.latency?.message}
                  {...register('latency')}
                />
              </div>
            </div>
          )}

          {/* Quality Rules — hidden for Tier 4 */}
          {tierShowsQuality(tier) && (
            <div className="space-y-3">
              <SectionHeader
                label={`${stepPrefix(5)}Quality Rules`}
                required={tierRequiresQuality(tier)}
                optional={!tierRequiresQuality(tier)}
              />
              <p className="text-xs text-gray-400 dark:text-slate-500">
                dimension · column (opt.) · operator · threshold · description
              </p>
              <QualityRules rules={quality} onChange={setQuality} />
              {qualityError && <p className="text-xs text-red-500 mt-1">{qualityError}</p>}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2 border-t border-gray-200 dark:border-slate-700">
            <Button type="button" variant="secondary" onClick={onCancel}>
              Cancel
            </Button>
            <Button type="submit" loading={isSubmitting}>
              {defaultValues ? 'Save Changes' : 'Create Contract'}
            </Button>
          </div>
        </>
      )}

      {/* Wizard shown but not yet done — only show Cancel */}
      {showWizard && !tierDone && (
        <div className="flex justify-end pt-2">
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      )}
    </form>
  )
}
