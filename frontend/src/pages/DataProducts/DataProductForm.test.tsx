import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import DataProductForm from './DataProductForm'
import type { DataProduct } from '../../types'

const existing: DataProduct = {
  id: 'prod-1',
  name: 'Existing Product',
  description: 'An existing data product description',
  data_contracts_id: '11111111-1111-1111-1111-111111111111',
  repo_url: null,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('DataProductForm', () => {
  it('renders the create button label without defaultValues', () => {
    render(
      <DataProductForm onSubmit={vi.fn()} onCancel={vi.fn()} isSubmitting={false} />,
    )
    expect(screen.getByRole('button', { name: 'Create Product' })).toBeInTheDocument()
  })

  it('renders the save label and prefilled values in edit mode', () => {
    render(
      <DataProductForm
        defaultValues={existing}
        onSubmit={vi.fn()}
        onCancel={vi.fn()}
        isSubmitting={false}
      />,
    )
    expect(screen.getByRole('button', { name: 'Save Changes' })).toBeInTheDocument()
    expect(screen.getByLabelText('Name')).toHaveValue('Existing Product')
  })

  it('calls onCancel when Cancel is clicked', () => {
    const onCancel = vi.fn()
    render(
      <DataProductForm onSubmit={vi.fn()} onCancel={onCancel} isSubmitting={false} />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(onCancel).toHaveBeenCalledOnce()
  })

  it('shows validation errors and does not submit invalid data', async () => {
    const onSubmit = vi.fn()
    render(
      <DataProductForm onSubmit={onSubmit} onCancel={vi.fn()} isSubmitting={false} />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Create Product' }))
    expect(
      await screen.findByText('Name must be at least 3 characters'),
    ).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('submits sanitized values when the form is valid', async () => {
    const onSubmit = vi.fn()
    render(
      <DataProductForm onSubmit={onSubmit} onCancel={vi.fn()} isSubmitting={false} />,
    )
    fireEvent.change(screen.getByLabelText('Name'), {
      target: { value: 'Valid Name' },
    })
    fireEvent.change(screen.getByLabelText('Description'), {
      target: { value: 'A sufficiently long description' },
    })
    fireEvent.change(screen.getByLabelText('Data Contract ID'), {
      target: { value: '22222222-2222-2222-2222-222222222222' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Create Product' }))
    await waitFor(() => expect(onSubmit).toHaveBeenCalledOnce())
    expect(onSubmit.mock.calls[0][0]).toMatchObject({
      name: 'Valid Name',
      description: 'A sufficiently long description',
      data_contracts_id: '22222222-2222-2222-2222-222222222222',
    })
  })
})
