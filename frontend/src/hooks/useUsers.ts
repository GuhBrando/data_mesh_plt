import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { get, post, put, del } from '../lib/api'
import type { User, UserFormData } from '../types'

const KEYS = {
  all: ['users'] as const,
  one: (id: string) => ['users', id] as const,
}

// ---- Queries ----

export function useUsers() {
  return useQuery<User[]>({
    queryKey: KEYS.all,
    queryFn: () => get<User[]>('/users'),
  })
}

export function useUser(id: string) {
  return useQuery<User>({
    queryKey: KEYS.one(id),
    queryFn: () => get<User>(`/users/${id}`),
    enabled: !!id,
  })
}

// ---- Mutations ----

export function useCreateUser() {
  const qc = useQueryClient()
  return useMutation<User, Error, UserFormData>({
    mutationFn: (data) => post<User>('/users', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
    },
  })
}

export function useUpdateUser() {
  const qc = useQueryClient()
  return useMutation<User, Error, { id: string } & UserFormData>({
    mutationFn: ({ id, ...data }) => put<User>(`/users/${id}`, data),
    onSuccess: (updated) => {
      qc.invalidateQueries({ queryKey: KEYS.all })
      qc.invalidateQueries({ queryKey: KEYS.one(updated.id) })
    },
  })
}

export function useDeleteUser() {
  const qc = useQueryClient()
  return useMutation<void, Error, string>({
    mutationFn: (id) => del(`/users/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEYS.all })
    },
  })
}
