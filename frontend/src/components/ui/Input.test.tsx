import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import Input, { Textarea } from './Input'

describe('Input', () => {
  it('renders without a label', () => {
    render(<Input placeholder="email" />)
    expect(screen.getByPlaceholderText('email')).toBeInTheDocument()
  })

  it('renders a label and links it via derived id', () => {
    render(<Input label="Full Name" />)
    const input = screen.getByLabelText('Full Name')
    expect(input).toHaveAttribute('id', 'full-name')
  })

  it('uses an explicit id over the derived one', () => {
    render(<Input label="Full Name" id="custom" />)
    expect(screen.getByLabelText('Full Name')).toHaveAttribute('id', 'custom')
  })

  it('shows an error message and error class', () => {
    render(<Input label="Email" error="Required" />)
    expect(screen.getByText('Required')).toHaveClass('form-error')
    expect(screen.getByLabelText('Email')).toHaveClass('error')
  })
})

describe('Textarea', () => {
  it('renders with a label and default rows', () => {
    render(<Textarea label="Notes" />)
    const area = screen.getByLabelText('Notes')
    expect(area).toHaveAttribute('rows', '5')
  })

  it('honors a custom rows value', () => {
    render(<Textarea label="Notes" rows={10} />)
    expect(screen.getByLabelText('Notes')).toHaveAttribute('rows', '10')
  })

  it('renders an error message', () => {
    render(<Textarea label="Notes" error="Too long" />)
    expect(screen.getByText('Too long')).toHaveClass('form-error')
  })
})
