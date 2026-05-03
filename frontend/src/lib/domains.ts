import type { DomainWithMembers, DomainAccess } from '../types'

export function getDomainAccess(domain: DomainWithMembers, userId: string): DomainAccess {
  if (domain.owner_id === userId) return 'owner'
  const member = domain.members.find((m) => m.user_id === userId)
  if (!member) return 'none'
  return member.role
}
