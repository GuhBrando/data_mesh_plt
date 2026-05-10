import { describe, it, expect } from 'vitest'
import { getDomainAccess } from './domains'
import type { DomainWithMembers } from '../types'

const domain: DomainWithMembers = {
  id: '1',
  name: 'Analytics',
  description: 'Core analytics',
  owner_id: 'user-alice',
  owner_username: 'alice',
  members: [
    { user_id: 'user-bob', username: 'bob', role: 'maintainer' },
    { user_id: 'user-carol', username: 'carol', role: 'member' },
  ],
  contract_count: 2,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
}

describe('getDomainAccess', () => {
  it('returns "owner" for the domain owner', () => {
    expect(getDomainAccess(domain, 'user-alice')).toBe('owner')
  })

  it('returns "maintainer" for a maintainer member', () => {
    expect(getDomainAccess(domain, 'user-bob')).toBe('maintainer')
  })

  it('returns "member" for a regular member', () => {
    expect(getDomainAccess(domain, 'user-carol')).toBe('member')
  })

  it('returns "none" for a user not in the domain', () => {
    expect(getDomainAccess(domain, 'user-dave')).toBe('none')
  })

  it('owner check takes precedence even if owner is also listed as a member', () => {
    const d: DomainWithMembers = {
      ...domain,
      members: [
        ...domain.members,
        { user_id: 'user-alice', username: 'alice', role: 'member' },
      ],
    }
    expect(getDomainAccess(d, 'user-alice')).toBe('owner')
  })

  it('returns "admin" for a PLATFORM_ADMIN regardless of domain membership', () => {
    expect(getDomainAccess(domain, 'user-dave', 'PLATFORM_ADMIN')).toBe('admin')
  })

  it('returns "admin" for a PLATFORM_ADMIN even when they are the domain owner', () => {
    expect(getDomainAccess(domain, 'user-alice', 'PLATFORM_ADMIN')).toBe('admin')
  })

  it('returns "owner" without userRole argument (backward-compatible)', () => {
    expect(getDomainAccess(domain, 'user-alice')).toBe('owner')
  })
})
