import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { MemoryRouter } from 'react-router-dom'
import PageHeader from './PageHeader'

const navigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => navigate }
})

function renderHeader(ui: React.ReactElement) {
  return render(<MemoryRouter>{ui}</MemoryRouter>)
}

describe('PageHeader', () => {
  it('renders the title', () => {
    renderHeader(<PageHeader title="Products" />)
    expect(screen.getByRole('heading', { name: 'Products' })).toBeInTheDocument()
  })

  it('renders the subtitle when provided', () => {
    renderHeader(<PageHeader title="Products" subtitle="All products" />)
    expect(screen.getByText('All products')).toBeInTheDocument()
  })

  it('renders actions when provided', () => {
    renderHeader(<PageHeader title="Products" actions={<button>New</button>} />)
    expect(screen.getByRole('button', { name: 'New' })).toBeInTheDocument()
  })

  it('does not render a back button without backTo', () => {
    renderHeader(<PageHeader title="Products" />)
    expect(screen.queryByLabelText('Go back')).not.toBeInTheDocument()
  })

  it('navigates to backTo when the back button is clicked', () => {
    navigate.mockClear()
    renderHeader(<PageHeader title="Detail" backTo="/products" />)
    fireEvent.click(screen.getByLabelText('Go back'))
    expect(navigate).toHaveBeenCalledWith('/products')
  })
})
