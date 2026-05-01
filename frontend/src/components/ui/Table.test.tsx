import { render, screen, fireEvent } from '@testing-library/react'
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

  it('fires onRowClick when a card is clicked', () => {
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
    const cards = screen.getAllByTestId('mobile-card')
    fireEvent.click(cards[0])
    expect(handleClick).toHaveBeenCalledWith(data[0])
  })

  it('fires onRowClick when a table row is clicked (no mobileCardConfig)', () => {
    const handleClick = vi.fn()
    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(r) => r.name}
        onRowClick={handleClick}
      />
    )
    // rows[0] is the header row, rows[1] is the first data row
    const rows = screen.getAllByRole('row')
    fireEvent.click(rows[1])
    expect(handleClick).toHaveBeenCalledWith(data[0])
  })

  it('renders badge column when mobileCardConfig includes badgeKey', () => {
    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(r) => r.name}
        mobileCardConfig={{ titleKey: 'name', badgeKey: 'email' }}
      />
    )
    expect(screen.getAllByTestId('mobile-card')).toHaveLength(2)
  })

  it('fires onRowClick on Enter key in mobile card', () => {
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
    const cards = screen.getAllByTestId('mobile-card')
    fireEvent.keyDown(cards[0], { key: 'Enter' })
    expect(handleClick).toHaveBeenCalledWith(data[0])
  })

  it('fires onRowClick on Space key in mobile card', () => {
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
    const cards = screen.getAllByTestId('mobile-card')
    fireEvent.keyDown(cards[0], { key: ' ' })
    expect(handleClick).toHaveBeenCalledWith(data[0])
  })

  it('ignores non-Enter/Space keys in mobile card', () => {
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
    const cards = screen.getAllByTestId('mobile-card')
    fireEvent.keyDown(cards[0], { key: 'Tab' })
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('renders empty state message in table when data is empty', () => {
    render(
      <Table
        columns={columns}
        data={[]}
        keyExtractor={(r) => r.name}
        emptyMessage="Nothing here"
      />
    )
    expect(screen.getByText('Nothing here')).toBeInTheDocument()
  })

  it('renders empty state message in cards when data is empty with mobileCardConfig', () => {
    render(
      <Table
        columns={columns}
        data={[]}
        keyExtractor={(r) => r.name}
        emptyMessage="No records"
        mobileCardConfig={{ titleKey: 'name' }}
      />
    )
    // Appears once in table, once in card list
    expect(screen.getAllByText('No records')).toHaveLength(2)
  })
})
