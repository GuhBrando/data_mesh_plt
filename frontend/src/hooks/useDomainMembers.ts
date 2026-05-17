import { useMutation, useQueryClient } from '@tanstack/react-query'
import { post, patch, del } from '../lib/api'
import type { DomainMember } from '../types'

const KEYS = {
  all: ['domains'] as const,
}

export interface AddMemberInput {
  user_id: string
  role: 'maintainer' | 'member'
}

export function useAddDomainMember(domainId: string) {
  const qc = useQueryClient()
  return useMutation<DomainMember, Error, AddMemberInput>({
    mutationFn: (data) => post<DomainMember>(`/domains/${domainId}/members`, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}

export function useUpdateDomainMember(domainId: string) {
  const qc = useQueryClient()
  return useMutation<DomainMember, Error, { userId: string; role: 'maintainer' | 'member' }>({
    mutationFn: ({ userId, role }) =>
      patch<DomainMember>(`/domains/${domainId}/members/${userId}`, { role }),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}

export function useRemoveDomainMember(domainId: string) {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (userId) => del(`/domains/${domainId}/members/${userId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}
