import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import Table from './Table'

const columns = [
  { key: 'name', header: 'Name', render: (row: { name: string }) => <span>{row.name}</span> },
  { key: 'email', header: 'Email', render: (row: { email: string }) => <span>{row.email}</span> },
  { key: 'actions', header: '', render: () => <button>Delete</button> },
]

const data = [
  { name: 'Alice', email: 'alice@example.com' },
  { name: 'Bob', email: 'bob@example.com' },
]

describe('Table', () => {
  it('renders a table when mobileCardConfig is not provided', () => {
    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(r) => r.name}
      />
    )
    expect(screen.getByRole('table')).toBeInTheDocument()
  })

  it('renders mobile cards when mobileCardConfig is provided', () => {
    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(r) => r.name}
        mobileCardConfig={{ titleKey: 'name' }}
      />
    )
    // Both table (desktop) and cards (mobile) are in the DOM — CSS hides one
    expect(screen.getByRole('table')).toBeInTheDocument()
    // Card titles appear
    expect(screen.getAllByText('Alice')).toHaveLength(2) // once in table, once in card
    expect(screen.getAllByText('Bob')).toHaveLength(2)
  })

  it('fires onRowClick when a card is clicked', async () => {
    const handleClick = vi.fn()
    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(r) => r.name}
        onRowClick={handleClick}
        mobileCardConfig={{ titleKey: 'name' }}
      />
    )
    const cards = document.querySelectorAll('[data-testid="mobile-card"]')
    ;(cards[0] as HTMLElement).click()
    expect(handleClick).toHaveBeenCalledWith(data[0])
  })
})
