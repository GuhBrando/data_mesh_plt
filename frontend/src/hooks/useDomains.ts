import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, put, del } from '../lib/api'
import type { DomainWithMembers, DomainInput } from '../types'

const KEYS = {
  all: ['domains'] as const,
  one: (id: string) => ['domains', id] as const,
}

export function useAllDomains() {
  return useQuery<DomainWithMembers[]>({
    queryKey: KEYS.all,
    queryFn: () => get<DomainWithMembers[]>('/domains'),
  })
}

export function useCreateDomain() {
  const qc = useQueryClient()
  return useMutation<DomainWithMembers, Error, DomainInput>({
    mutationFn: (data) => post<DomainWithMembers>('/domains', data),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}

export function useUpdateDomain() {
  const qc = useQueryClient()
  return useMutation<DomainWithMembers, Error, { id: string } & Partial<DomainInput>>({
    mutationFn: ({ id, ...body }) => put<DomainWithMembers>(`/domains/${id}`, body),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: KEYS.all })
      qc.invalidateQueries({ queryKey: KEYS.one(updated.id) })
    },
  })
}

export function useDeleteDomain() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (id) => del(`/domains/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: KEYS.all }),
  })
}
