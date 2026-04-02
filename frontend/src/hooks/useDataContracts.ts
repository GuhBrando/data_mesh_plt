import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, put, del } from '../lib/api'
import type { DataContract } from '../types'

const KEYS = {
  all: ['data-contracts'] as const,
  one: (id: string) => ['data-contracts', id] as const,
}

// ---- Queries ----

export function useDataContracts() {
  return useQuery<DataContract[]>({
    queryKey: KEYS.all,
    queryFn: () => get<DataContract[]>('/data-contracts'),
  })
}

export function useDataContract(id: string) {
  return useQuery<DataContract>({
    queryKey: KEYS.one(id),
    queryFn: () => get<DataContract>(`/data-contracts/${id}`),
    enabled: !!id,
  })
}

// ---- Mutations ----

export function useCreateDataContract() {
  const qc = useQueryClient()
  return useMutation<DataContract, Error, Record<string, unknown>>({
    mutationFn: (obj) => post<DataContract>('/data-contracts', { obj }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
    },
  })
}

export function useUpdateDataContract() {
  const qc = useQueryClient()
  return useMutation<
    DataContract,
    Error,
    { id: string; obj: Record<string, unknown> }
  >({
    mutationFn: ({ id, obj }) =>
      put<DataContract>(`/data-contracts/${id}`, { obj }),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: KEYS.all })
      qc.invalidateQueries({ queryKey: KEYS.one(updated.id) })
    },
  })
}

export function useDeleteDataContract() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (id) => del(`/data-contracts/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
    },
  })
}
