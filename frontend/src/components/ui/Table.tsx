import { ReactNode } from 'react'

interface Column<T> {
  key: string
  header: string
  render: (row: T) => ReactNode
  className?: string
}

interface MobileCardConfig {
  titleKey: string
  badgeKey?: string
}

interface TableProps<T> {
  columns: Column<T>[]
  data: T[]
  onRowClick?: (row: T) => void
  keyExtractor: (row: T) => string
  emptyMessage?: string
  mobileCardConfig?: MobileCardConfig
}

export default function Table<T>({
  columns,
  data,
  onRowClick,
  keyExtractor,
  emptyMessage = 'No records found.',
  mobileCardConfig,
}: TableProps<T>) {
  const tableNode = (
    <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-slate-700">
      <table className="min-w-full divide-y divide-gray-100 dark:divide-slate-700">
        <thead>
          <tr className="bg-gray-50 dark:bg-slate-700/50">
            {columns.map((col) => (
              <th
                key={col.key}
                scope="col"
                className={`px-4 py-3 text-left text-xs font-semibold text-gray-500 dark:text-slate-400 uppercase tracking-wider ${col.className ?? ''}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white dark:bg-slate-800 divide-y divide-gray-100 dark:divide-slate-700">
          {data.length === 0 ? (
            <tr>
              <td
                colSpan={columns.length}
                className="px-4 py-12 text-center text-sm text-gray-400 dark:text-slate-500"
              >
                {emptyMessage}
              </td>
            </tr>
          ) : (
            data.map((row) => (
              <tr
                key={keyExtractor(row)}
                onClick={onRowClick ? () => onRowClick(row) : undefined}
                className={`transition-colors ${
                  onRowClick
                    ? 'cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20'
                    : 'hover:bg-gray-50 dark:hover:bg-slate-700'
                }`}
              >
                {columns.map((col) => (
                  <td
                    key={col.key}
                    className={`px-4 py-3 text-sm text-gray-700 dark:text-slate-300 ${col.className ?? ''}`}
                  >
                    {col.render(row)}
                  </td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )

  if (!mobileCardConfig) return tableNode

  const titleCol = columns.find((c) => c.key === mobileCardConfig.titleKey)
  if (import.meta.env.DEV && !titleCol) {
    console.warn(`[Table] mobileCardConfig.titleKey "${mobileCardConfig.titleKey}" does not match any column key`)
  }
  const badgeCol = mobileCardConfig.badgeKey
    ? columns.find((c) => c.key === mobileCardConfig.badgeKey)
    : undefined
  const bodyColumns = columns.filter(
    (c) =>
      c.key !== mobileCardConfig.titleKey &&
      c.key !== mobileCardConfig.badgeKey &&
      c.header !== '',
  )
  const actionColumns = columns.filter(
    (c) => c.header === '' && c.key !== mobileCardConfig.badgeKey,
  )

  const cardListNode = (
    <div className="md:hidden space-y-3">
      {data.length === 0 ? (
        <p className="py-12 text-center text-sm text-gray-400 dark:text-slate-500">
          {emptyMessage}
        </p>
      ) : (
        data.map((row) => (
          <div
            key={keyExtractor(row)}
            data-testid="mobile-card"
            onClick={onRowClick ? () => onRowClick(row) : undefined}
            role={onRowClick ? 'button' : undefined}
            tabIndex={onRowClick ? 0 : undefined}
            onKeyDown={onRowClick ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault()
                onRowClick(row)
              }
            } : undefined}
            className={`bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-xl p-4 transition-colors ${
              onRowClick
                ? 'cursor-pointer hover:bg-blue-50 dark:hover:bg-blue-900/20'
                : ''
            }`}
          >
            <div className="flex items-start justify-between gap-2 mb-3">
              <div className="font-medium text-gray-900 dark:text-slate-100 min-w-0">
                {titleCol?.render(row)}
              </div>
              {badgeCol && <div className="shrink-0">{badgeCol.render(row)}</div>}
            </div>
            {bodyColumns.length > 0 && (
              <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                {bodyColumns.map((col) => (
                  <div key={col.key}>
                    <div className="text-xs font-semibold text-gray-400 dark:text-slate-500 uppercase tracking-wider mb-0.5">
                      {col.header}
                    </div>
                    <div className="text-sm text-gray-700 dark:text-slate-300">
                      {col.render(row)}
                    </div>
                  </div>
                ))}
              </div>
            )}
            {actionColumns.map((col) => (
              <div
                key={col.key}
                className="mt-3 pt-3 border-t border-gray-100 dark:border-slate-700 flex justify-end"
              >
                {col.render(row)}
              </div>
            ))}
          </div>
        ))
      )}
    </div>
  )

  return (
    <>
      <div className="hidden md:block">{tableNode}</div>
      {cardListNode}
    </>
  )
}
