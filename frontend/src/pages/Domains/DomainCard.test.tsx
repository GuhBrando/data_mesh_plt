import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import DomainCard from './DomainCard'
import type { DomainWithMembers } from '../../types'

const domain: DomainWithMembers = {
  id: '1',
  name: 'Analytics',
  description: 'Core analytics domain',
  owner_id: 'user-alice',
  owner_username: 'alice',
  members: [{ user_id: 'user-bob', username: 'bob', role: 'member' }],
  contract_count: 3,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('DomainCard', () => {
  it('renders the domain name', () => {
    render(<DomainCard domain={domain} access="member" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('Analytics')).toBeInTheDocument()
  })

  it('renders the description', () => {
    render(<DomainCard domain={domain} access="member" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('Core analytics domain')).toBeInTheDocument()
  })

  it('renders "Owner" badge when access is owner', () => {
    render(<DomainCard domain={domain} access="owner" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('Owner')).toBeInTheDocument()
    expect(screen.getByTestId('domain-card')).toHaveAttribute('data-access', 'owner')
  })

  it('renders "Maintainer" badge when access is maintainer', () => {
    render(<DomainCard domain={domain} access="maintainer" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('Maintainer')).toBeInTheDocument()
  })

  it('renders "Member" badge when access is member', () => {
    render(<DomainCard domain={domain} access="member" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('Member')).toBeInTheDocument()
  })

  it('renders "No Access" badge when access is none', () => {
    render(<DomainCard domain={domain} access="none" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('No Access')).toBeInTheDocument()
  })

  it('calls onClick when the card is clicked', () => {
    const handleClick = vi.fn()
    render(<DomainCard domain={domain} access="member" isSelected={false} onClick={handleClick} />)
    fireEvent.click(screen.getByTestId('domain-card'))
    expect(handleClick).toHaveBeenCalledOnce()
  })

  it('shows member count', () => {
    render(<DomainCard domain={domain} access="member" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('shows contract count', () => {
    render(<DomainCard domain={domain} access="member" isSelected={false} onClick={vi.fn()} />)
    expect(screen.getByText('3')).toBeInTheDocument()
  })
})
