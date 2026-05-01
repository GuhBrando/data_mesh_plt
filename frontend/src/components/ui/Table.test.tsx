import { render, screen, fireEvent, within } from '@testing-library/react'
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

  it('uses "No records found." as default empty message', () => {
    render(<Table columns={columns} data={[]} keyExtractor={(r) => r.name} />)
    expect(screen.getByText('No records found.')).toBeInTheDocument()
  })

  it('mobile cards have no role or tabIndex when onRowClick is absent', () => {
    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(r) => r.name}
        mobileCardConfig={{ titleKey: 'name' }}
      />
    )
    const cards = screen.getAllByTestId('mobile-card')
    expect(cards[0]).not.toHaveAttribute('role')
    expect(cards[0]).not.toHaveAttribute('tabIndex')
  })

  it('renders action columns (empty header) at bottom of mobile cards', () => {
    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(r) => r.name}
        mobileCardConfig={{ titleKey: 'name' }}
      />
    )
    const cards = screen.getAllByTestId('mobile-card')
    // 'actions' column has header='' → rendered as action, not body
    expect(within(cards[0]).getByRole('button', { name: 'Delete' })).toBeInTheDocument()
  })

  it('renders body column header labels inside mobile cards', () => {
    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(r) => r.name}
        mobileCardConfig={{ titleKey: 'name' }}
      />
    )
    const cards = screen.getAllByTestId('mobile-card')
    // 'email' has header='Email' → body grid label appears in card
    expect(within(cards[0]).getByText('Email')).toBeInTheDocument()
  })

  it('excludes title column from body grid in mobile cards', () => {
    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(r) => r.name}
        mobileCardConfig={{ titleKey: 'name' }}
      />
    )
    const cards = screen.getAllByTestId('mobile-card')
    // 'Name' is the titleKey — its header label must NOT appear in the body grid
    expect(within(cards[0]).queryByText('Name')).not.toBeInTheDocument()
  })

  it('excludes badgeKey column from body grid in mobile cards', () => {
    render(
      <Table
        columns={columns}
        data={data}
        keyExtractor={(r) => r.name}
        mobileCardConfig={{ titleKey: 'name', badgeKey: 'email' }}
      />
    )
    const cards = screen.getAllByTestId('mobile-card')
    // 'email' is now the badgeKey — its header 'Email' must NOT appear in body grid
    expect(within(cards[0]).queryByText('Email')).not.toBeInTheDocument()
  })

  it('shows no body grid labels when all columns are title or action', () => {
    const minCols = [
      { key: 'id', header: 'ID', render: (r: { id: string }) => <span>{r.id}</span> },
      { key: 'del', header: '', render: () => <button>Del</button> },
    ]
    render(
      <Table
        columns={minCols}
        data={[{ id: '1' }]}
        keyExtractor={(r) => r.id}
        mobileCardConfig={{ titleKey: 'id' }}
      />
    )
    const cards = screen.getAllByTestId('mobile-card')
    // 'id' is titleKey (excluded from body) and 'del' has empty header (action)
    // So bodyColumns is empty — 'ID' header label must not appear in body grid
    expect(within(cards[0]).queryByText('ID')).not.toBeInTheDocument()
  })
})
