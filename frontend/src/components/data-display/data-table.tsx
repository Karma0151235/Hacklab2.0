'use client'

import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/lib/utils'

interface Column<T> {
  key: string
  label: string
  sortable?: boolean
  render?: (item: T) => React.ReactNode
  className?: string
}

interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  keyExtractor: (item: T) => string
  itemsPerPage?: number
  searchable?: boolean
  className?: string
}

type SortConfig = {
  key: string
  direction: 'asc' | 'desc'
} | null

export function DataTable<T extends Record<string, any>>({
  data,
  columns,
  keyExtractor,
  itemsPerPage = 10,
  className,
}: DataTableProps<T>) {
  const [sortConfig, setSortConfig] = useState<SortConfig>(null)
  const [currentPage, setCurrentPage] = useState(1)

  // Sorting logic
  const sortedData = [...data].sort((a, b) => {
    if (!sortConfig) return 0

    const aValue = a[sortConfig.key]
    const bValue = b[sortConfig.key]

    if (aValue === bValue) return 0

    const comparison = aValue > bValue ? 1 : -1
    return sortConfig.direction === 'asc' ? comparison : -comparison
  })

  // Pagination logic
  const totalPages = Math.ceil(sortedData.length / itemsPerPage)
  const startIndex = (currentPage - 1) * itemsPerPage
  const endIndex = startIndex + itemsPerPage
  const paginatedData = sortedData.slice(startIndex, endIndex)

  const handleSort = (key: string) => {
    setSortConfig((current) => {
      if (!current || current.key !== key) {
        return { key, direction: 'asc' }
      }
      if (current.direction === 'asc') {
        return { key, direction: 'desc' }
      }
      return null
    })
  }

  const getSortIcon = (key: string) => {
    if (!sortConfig || sortConfig.key !== key) {
      return <ArrowUpDown className="h-4 w-4" />
    }
    return sortConfig.direction === 'asc' ? (
      <ArrowUp className="h-4 w-4" />
    ) : (
      <ArrowDown className="h-4 w-4" />
    )
  }

  return (
    <div className={cn('rounded-lg border border-border-primary bg-bg-secondary', className)}>
      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border-secondary bg-bg-elevated">
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={cn(
                    'px-6 py-4 text-left font-mono text-xs font-bold uppercase tracking-wider text-text-secondary',
                    column.sortable && 'cursor-pointer select-none hover:text-accent-primary',
                    column.className
                  )}
                  onClick={() => column.sortable && handleSort(column.key)}
                >
                  <div className="flex items-center gap-2">
                    <span>{column.label}</span>
                    {column.sortable && getSortIcon(column.key)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border-secondary">
            {paginatedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-6 py-12 text-center font-sans text-sm text-text-tertiary"
                >
                  No data available
                </td>
              </tr>
            ) : (
              paginatedData.map((item) => (
                <tr
                  key={keyExtractor(item)}
                  className="transition-colors hover:bg-bg-elevated"
                >
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={cn(
                        'px-6 py-4 font-sans text-sm text-text-primary',
                        column.className
                      )}
                    >
                      {column.render
                        ? column.render(item)
                        : item[column.key]?.toString() || '-'}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-border-secondary bg-bg-tertiary px-6 py-4">
          <div className="font-mono text-sm text-text-secondary">
            Showing{' '}
            <span className="font-semibold text-text-primary">
              {startIndex + 1}
            </span>{' '}
            to{' '}
            <span className="font-semibold text-text-primary">
              {Math.min(endIndex, sortedData.length)}
            </span>{' '}
            of{' '}
            <span className="font-semibold text-text-primary">
              {sortedData.length}
            </span>{' '}
            results
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="flex items-center gap-1 rounded-md border border-border-secondary bg-bg-secondary px-3 py-2 font-mono text-xs font-semibold text-text-secondary transition-all hover:border-accent-primary/40 hover:text-accent-primary disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-border-secondary disabled:hover:text-text-secondary"
            >
              <ChevronLeft className="h-4 w-4" />
              <span>Previous</span>
            </button>

            <div className="flex items-center gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={cn(
                    'h-10 w-10 rounded-md border font-mono text-xs font-semibold transition-all',
                    currentPage === page
                      ? 'border-accent-primary bg-accent-primary/10 text-accent-primary'
                      : 'border-border-secondary bg-bg-secondary text-text-secondary hover:border-accent-primary/40 hover:text-accent-primary'
                  )}
                >
                  {page}
                </button>
              ))}
            </div>

            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="flex items-center gap-1 rounded-md border border-border-secondary bg-bg-secondary px-3 py-2 font-mono text-xs font-semibold text-text-secondary transition-all hover:border-accent-primary/40 hover:text-accent-primary disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-border-secondary disabled:hover:text-text-secondary"
            >
              <span>Next</span>
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
