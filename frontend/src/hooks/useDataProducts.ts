import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, put, del } from '../lib/api'
import type { DataProduct, DataProductFormData } from '../types'

const KEYS = {
  all: ['data-products'] as const,
  one: (id: string) => ['data-products', id] as const,
}

// ---- Queries ----

export function useDataProducts() {
  return useQuery<DataProduct[]>({
    queryKey: KEYS.all,
    queryFn: () => get<DataProduct[]>('/data-products'),
  })
}

export function useDataProduct(id: string) {
  return useQuery<DataProduct>({
    queryKey: KEYS.one(id),
    queryFn: () => get<DataProduct>(`/data-products/${id}`),
    enabled: !!id,
  })
}

// ---- Mutations ----

export function useCreateDataProduct() {
  const qc = useQueryClient()
  return useMutation<DataProduct, Error, DataProductFormData>({
    mutationFn: (data) => post<DataProduct>('/data-products', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
    },
  })
}

export function useUpdateDataProduct() {
  const qc = useQueryClient()
  return useMutation<
    DataProduct,
    Error,
    { id: string } & DataProductFormData
  >({
    mutationFn: ({ id, ...data }) =>
      put<DataProduct>(`/data-products/${id}`, data),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: KEYS.all })
      qc.invalidateQueries({ queryKey: KEYS.one(updated.id) })
    },
  })
}

export function useDeleteDataProduct() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (id) => del(`/data-products/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
    },
  })
}
