import { useRef } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import type { QualityRule } from '../../types'

const DIMENSIONS = ['completeness', 'freshness', 'uniqueness', 'validity', 'integrity'] as const
const OPERATORS = ['>=', '<=', '='] as const

interface QualityRulesProps {
  rules: QualityRule[]
  onChange: (rules: QualityRule[]) => void
}

const emptyRule = (): QualityRule => ({
  dimension: 'completeness',
  column: '',
  operator: '>=',
  threshold: '',
  description: '',
})

export default function QualityRules({ rules, onChange }: QualityRulesProps) {
  const idsRef = useRef<string[]>([])
  const getKey = (index: number): string => {
    while (idsRef.current.length <= index) idsRef.current.push(crypto.randomUUID())
    return idsRef.current[index]
  }

  const update = (index: number, patch: Partial<QualityRule>) => {
    onChange(rules.map((r, i) => (i === index ? { ...r, ...patch } : r)))
  }

  const add = () => onChange([...rules, emptyRule()])

  const remove = (index: number) => {
    idsRef.current.splice(index, 1)
    onChange(rules.filter((_, i) => i !== index))
  }

  return (
    <div className="space-y-3">
      {rules.length === 0 && (
        <p className="text-sm text-gray-400 dark:text-slate-500 italic">No quality rules yet.</p>
      )}
      {rules.map((rule, i) => (
        <div
          key={getKey(i)}
          className="grid grid-cols-12 gap-2 items-center rounded border border-gray-200 dark:border-slate-700 p-2 bg-gray-50 dark:bg-slate-900"
        >
          {/* Dimension */}
          <select
            className="col-span-2 text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
            value={rule.dimension}
            onChange={(e) => update(i, { dimension: e.target.value as QualityRule['dimension'] })}
          >
            {DIMENSIONS.map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
          {/* Column */}
          <input
            className="col-span-2 text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
            placeholder="column (opt.)"
            value={rule.column}
            onChange={(e) => update(i, { column: e.target.value })}
          />
          {/* Operator */}
          <select
            className="col-span-1 text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
            value={rule.operator}
            onChange={(e) => update(i, { operator: e.target.value as QualityRule['operator'] })}
          >
            {OPERATORS.map((op) => (
              <option key={op} value={op}>{op}</option>
            ))}
          </select>
          {/* Threshold */}
          <input
            className="col-span-2 text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
            placeholder="99%, 24h, 0"
            value={rule.threshold}
            onChange={(e) => update(i, { threshold: e.target.value })}
          />
          {/* Description */}
          <input
            className="col-span-4 text-sm border border-gray-300 dark:border-slate-600 rounded px-2 py-1 bg-white dark:bg-slate-800 text-gray-800 dark:text-slate-200"
            placeholder="Description (optional)"
            value={rule.description}
            onChange={(e) => update(i, { description: e.target.value })}
          />
          {/* Remove */}
          <button
            type="button"
            onClick={() => remove(i)}
            className="col-span-1 flex items-center justify-center text-red-400 hover:text-red-600"
            title="Remove rule"
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
        Add rule
      </button>
    </div>
  )
}
