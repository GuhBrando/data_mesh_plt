import type { DomainWithMembers, DomainAccess } from '../types'

export function getDomainAccess(
  domain: DomainWithMembers,
  userId: string,
  userRole?: string,
): DomainAccess {
  if (userRole === 'PLATFORM_ADMIN') return 'admin'
  if (domain.owner_id === userId) return 'owner'
  const member = domain.members.find((m) => m.user_id === userId)
  if (!member) return 'none'
  return member.role
}
