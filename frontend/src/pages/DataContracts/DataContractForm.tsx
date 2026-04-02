import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Textarea } from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import type { DataContract } from '../../types'

const schema = z.object({
  obj: z.string().min(1, 'Contract JSON is required').superRefine((val, ctx) => {
    try {
      const parsed = JSON.parse(val)
      if (typeof parsed !== 'object' || Array.isArray(parsed) || parsed === null) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Must be a valid JSON object (not array or null)',
        })
      }
    } catch {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Invalid JSON — please check syntax',
      })
    }
  }),
})

type FormValues = z.infer<typeof schema>

interface DataContractFormProps {
  defaultValues?: DataContract
  onSubmit: (obj: Record<string, unknown>) => void
  onCancel: () => void
  isSubmitting: boolean
}

const PLACEHOLDER = JSON.stringify(
  {
    version: '1.0',
    schema: {
      type: 'object',
      properties: {
        id: { type: 'string' },
        name: { type: 'string' },
      },
    },
  },
  null,
  2,
)

export default function DataContractForm({
  defaultValues,
  onSubmit,
  onCancel,
  isSubmitting,
}: DataContractFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      obj: defaultValues ? JSON.stringify(defaultValues.obj, null, 2) : '',
    },
  })

  useEffect(() => {
    if (defaultValues) {
      setValue('obj', JSON.stringify(defaultValues.obj, null, 2))
    }
  }, [defaultValues, setValue])

  const handleFormSubmit = (values: FormValues) => {
    const parsed = JSON.parse(values.obj) as Record<string, unknown>
    onSubmit(parsed)
  }

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-5">
      <Textarea
        label="Contract Object (JSON)"
        placeholder={PLACEHOLDER}
        rows={12}
        error={errors.obj?.message}
        {...register('obj')}
      />
      <p className="text-xs text-gray-400">
        Enter a valid JSON object. This represents the contract schema or metadata.
      </p>

      <div className="flex justify-end gap-3 pt-2">
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
