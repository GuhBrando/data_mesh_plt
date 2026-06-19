import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Spinner from './Spinner'

describe('Spinner', () => {
  it('renders with the default medium size', () => {
    render(<Spinner />)
    expect(screen.getByLabelText('Loading')).toHaveClass('w-6', 'h-6')
  })

  it('applies the small size', () => {
    render(<Spinner size="sm" />)
    expect(screen.getByLabelText('Loading')).toHaveClass('w-4', 'h-4')
  })

  it('applies the large size and extra className', () => {
    render(<Spinner size="lg" className="mr-2" />)
    const svg = screen.getByLabelText('Loading')
    expect(svg).toHaveClass('w-10', 'h-10', 'mr-2')
  })
})
