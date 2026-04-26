import { Plus, Trash2 } from 'lucide-react'
import type { SchemaField } from '../../types'

const FIELD_TYPES = ['string', 'integer', 'float', 'boolean', 'date', 'timestamp'] as const

interface ContractFieldsProps {
  fields: SchemaField[]
  onChange: (fields: SchemaField[]) => void
}

const emptyField = (): SchemaField => ({
  name: '',
  type: 'string',
  description: '',
  nullable: true,
  primary_key: false,
})

export default function ContractFields({ fields, onChange }: ContractFieldsProps) {
  const update = (index: number, patch: Partial<SchemaField>) => {
    const next = fields.map((f, i) => (i === index ? { ...f, ...patch } : f))
    onChange(next)
  }

  const add = () => onChange([...fields, emptyField()])

  const remove = (index: number) => onChange(fields.filter((_, i) => i !== index))

  return (
    <div className="space-y-3">
      {fields.length === 0 && (
        <p className="text-sm text-gray-400 dark:text-slate-500 italic">No fields yet.</p>
      )}
      {fields.map((field, i) => (
        <div
          key={i}
          className="grid grid-cols-12 gap-2 items-center rounded border border-gray-200 dark:border-slate-700 p-2 bg-gray-50 dark:bg-slate-900"
        >
          {/* Name */}
          <input
            className="col-span-3 text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
            placeholder="field_name"
            value={field.name}
            onChange={(e) => update(i, { name: e.target.value })}
          />
          {/* Type */}
          <select
            className="col-span-2 text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
            value={field.type}
            onChange={(e) => update(i, { type: e.target.value as SchemaField['type'] })}
          >
            {FIELD_TYPES.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          {/* Description */}
          <input
            className="col-span-4 text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
            placeholder="Description"
            value={field.description}
            onChange={(e) => update(i, { description: e.target.value })}
          />
          {/* Nullable toggle */}
          <label className="col-span-1 flex items-center gap-1 text-xs text-gray-500 dark:text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={field.nullable}
              onChange={(e) => update(i, { nullable: e.target.checked })}
            />
            Null
          </label>
          {/* PK toggle */}
          <label className="col-span-1 flex items-center gap-1 text-xs text-gray-500 dark:text-slate-400 cursor-pointer">
            <input
              type="checkbox"
              checked={field.primary_key}
              onChange={(e) => update(i, { primary_key: e.target.checked })}
            />
            PK
          </label>
          {/* Remove */}
          <button
            type="button"
            onClick={() => remove(i)}
            className="col-span-1 flex items-center justify-center text-red-400 hover:text-red-600"
            title="Remove field"
          >
            <Trash2 size={14} />
          </button>
        </div>
      ))}
      <button
        type="button"
        onClick={add}
        className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400 hover:underline"
      >
        <Plus size={14} />
        Add field
      </button>
    </div>
  )
}
