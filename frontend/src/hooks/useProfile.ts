import { useQuery } from '@tanstack/react-query'
import { get } from '../lib/api'
import type { Domain } from '../types'

export function useUserDomains(userId: string | undefined) {
  return useQuery({
    queryKey: ['users', userId, 'domains'],
    queryFn: () => get<Domain[]>(`/users/${userId}/domains`),
    enabled: !!userId,
  })
}
