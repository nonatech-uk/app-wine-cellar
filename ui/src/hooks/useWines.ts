import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchWines, fetchWine, updateWine, fetchWineLog, addLogEntry, updateLogEntry, deleteLogEntry, fetchRecentLog, fetchOverview, fetchByCountry, fetchTimeline, fetchCellar, updateCellar, deleteCellar, fetchWishlist, updateWishlist, deleteWishlist, fetchMe } from '../api/wines.ts'
import type { WineFilters } from '../api/wines.ts'

export function useMe() {
  return useQuery({ queryKey: ['me'], queryFn: fetchMe })
}

export function useWines(filters: WineFilters) {
  return useQuery({ queryKey: ['wines', filters], queryFn: () => fetchWines(filters) })
}

export function useWine(id: number) {
  return useQuery({ queryKey: ['wine', id], queryFn: () => fetchWine(id) })
}

export function useUpdateWine() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) => updateWine(id, data),
    onSuccess: (_d, v) => {
      qc.invalidateQueries({ queryKey: ['wine', v.id] })
      qc.invalidateQueries({ queryKey: ['wines'] })
    },
  })
}

export function useWineLog(wineId: number) {
  return useQuery({ queryKey: ['wine-log', wineId], queryFn: () => fetchWineLog(wineId) })
}

export function useAddLog() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ wineId, data }: { wineId: number; data: Record<string, unknown> }) => addLogEntry(wineId, data),
    onSuccess: (_d, v) => {
      qc.invalidateQueries({ queryKey: ['wine-log', v.wineId] })
      qc.invalidateQueries({ queryKey: ['wine', v.wineId] })
      qc.invalidateQueries({ queryKey: ['recent-log'] })
      qc.invalidateQueries({ queryKey: ['overview'] })
    },
  })
}

export function useUpdateLog() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ logId, data }: { logId: number; data: Record<string, unknown> }) => updateLogEntry(logId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['wine-log'] })
      qc.invalidateQueries({ queryKey: ['recent-log'] })
    },
  })
}

export function useDeleteLog() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (logId: number) => deleteLogEntry(logId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['wine-log'] })
      qc.invalidateQueries({ queryKey: ['recent-log'] })
      qc.invalidateQueries({ queryKey: ['overview'] })
    },
  })
}

export function useRecentLog(limit = 20) {
  return useQuery({ queryKey: ['recent-log', limit], queryFn: () => fetchRecentLog(limit) })
}

export function useOverview() {
  return useQuery({ queryKey: ['overview'], queryFn: fetchOverview })
}

export function useByCountry() {
  return useQuery({ queryKey: ['by-country'], queryFn: fetchByCountry })
}

export function useTimeline() {
  return useQuery({ queryKey: ['timeline'], queryFn: fetchTimeline })
}

export function useCellar() {
  return useQuery({ queryKey: ['cellar'], queryFn: fetchCellar })
}

export function useUpdateCellar() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) => updateCellar(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cellar'] }) },
  })
}

export function useDeleteCellar() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteCellar(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['cellar'] }) },
  })
}

export function useWishlist() {
  return useQuery({ queryKey: ['wishlist'], queryFn: fetchWishlist })
}

export function useUpdateWishlist() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) => updateWishlist(id, data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['wishlist'] }) },
  })
}

export function useDeleteWishlist() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteWishlist(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['wishlist'] }) },
  })
}
