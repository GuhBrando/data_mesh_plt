import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Card, { CardHeader, CardTitle } from './Card'

describe('Card', () => {
  it('renders children', () => {
    render(<Card>content</Card>)
    expect(screen.getByText('content')).toBeInTheDocument()
  })

  it('applies padding by default', () => {
    render(<Card>padded</Card>)
    expect(screen.getByText('padded')).toHaveClass('p-6')
  })

  it('omits padding when padding is false', () => {
    render(<Card padding={false}>flush</Card>)
    expect(screen.getByText('flush')).not.toHaveClass('p-6')
  })

  it('forwards extra props and className', () => {
    render(
      <Card className="extra" data-testid="card">
        x
      </Card>,
    )
    expect(screen.getByTestId('card')).toHaveClass('extra')
  })
})

describe('CardHeader', () => {
  it('renders children', () => {
    render(<CardHeader>header</CardHeader>)
    expect(screen.getByText('header')).toBeInTheDocument()
  })

  it('merges custom className', () => {
    render(<CardHeader className="mine">header</CardHeader>)
    expect(screen.getByText('header')).toHaveClass('mine')
  })
})

describe('CardTitle', () => {
  it('renders a heading with children', () => {
    render(<CardTitle>title</CardTitle>)
    expect(screen.getByRole('heading', { name: 'title' })).toBeInTheDocument()
  })

  it('merges custom className', () => {
    render(<CardTitle className="mine">title</CardTitle>)
    expect(screen.getByText('title')).toHaveClass('mine')
  })
})
