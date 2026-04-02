import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Input } from '../../components/ui/Input'
import Button from '../../components/ui/Button'
import type { DataProduct } from '../../types'

const UUID_REGEX =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

const schema = z.object({
  name: z
    .string()
    .min(3, 'Name must be at least 3 characters'),
  description: z
    .string()
    .min(10, 'Description must be at least 10 characters'),
  data_contracts_id: z
    .string()
    .regex(UUID_REGEX, 'Must be a valid UUID (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)'),
})

type FormValues = z.infer<typeof schema>

interface DataProductFormProps {
  defaultValues?: DataProduct
  onSubmit: (values: FormValues) => void
  onCancel: () => void
  isSubmitting: boolean
}

export default function DataProductForm({
  defaultValues,
  onSubmit,
  onCancel,
  isSubmitting,
}: DataProductFormProps) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: defaultValues
      ? {
          name: defaultValues.name,
          description: defaultValues.description,
          data_contracts_id: defaultValues.data_contracts_id,
        }
      : { name: '', description: '', data_contracts_id: '' },
  })

  useEffect(() => {
    if (defaultValues) {
      reset({
        name: defaultValues.name,
        description: defaultValues.description,
        data_contracts_id: defaultValues.data_contracts_id,
      })
    }
  }, [defaultValues, reset])

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <Input
        label="Name"
        placeholder="My Data Product"
        error={errors.name?.message}
        {...register('name')}
      />

      <Input
        label="Description"
        placeholder="A detailed description of this data product..."
        error={errors.description?.message}
        {...register('description')}
      />

      <Input
        label="Data Contract ID"
        placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
        error={errors.data_contracts_id?.message}
        {...register('data_contracts_id')}
      />
      <p className="text-xs text-gray-400 -mt-3">
        The UUID of the associated data contract.
      </p>

      <div className="flex justify-end gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit" loading={isSubmitting}>
          {defaultValues ? 'Save Changes' : 'Create Product'}
        </Button>
      </div>
    </form>
  )
}
