import { useMutation, useQuery } from '@tanstack/react-query'
import { get, patch } from '../lib/api'
import type { Domain } from '../types'

export function useUserDomains(userId: string | undefined) {
  return useQuery({
    queryKey: ['users', userId, 'domains'],
    queryFn: () => get<Domain[]>(`/users/${userId}/domains`),
    enabled: !!userId,
  })
}

export function useChangePassword(userId: string) {
  return useMutation({
    mutationFn: (vars: { current_password: string; new_password: string }) =>
      patch<void>(`/users/${userId}/password`, vars),
  })
}
