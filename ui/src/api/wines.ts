import { apiFetch } from './client.ts'
import type { WineDetail, WineList, LogEntry, OverviewStats, CountryStat, TimelinePoint, CellarItem, WishlistItem, UserInfo } from './types.ts'

export function fetchMe() {
  return apiFetch<UserInfo>('/auth/me')
}

export interface WineFilters {
  q?: string
  country?: string
  wine_type?: string
  sort?: string
  limit?: number
  offset?: number
}

export function fetchWines(filters: WineFilters = {}) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '') params.set(k, String(v))
  })
  return apiFetch<WineList>(`/wines${params.toString() ? '?' + params : ''}`)
}

export function fetchWine(id: number) {
  return apiFetch<WineDetail>(`/wines/${id}`)
}

export function updateWine(id: number, data: Record<string, unknown>) {
  return apiFetch<WineDetail>(`/wines/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function fetchWineLog(wineId: number) {
  return apiFetch<LogEntry[]>(`/wines/${wineId}/log`)
}

export function addLogEntry(wineId: number, data: Record<string, unknown>) {
  return apiFetch<LogEntry>(`/wines/${wineId}/log`, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export function updateLogEntry(logId: number, data: Record<string, unknown>) {
  return apiFetch<LogEntry>(`/log/${logId}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deleteLogEntry(logId: number) {
  return apiFetch(`/log/${logId}`, { method: 'DELETE' })
}

export function fetchRecentLog(limit = 20) {
  return apiFetch<LogEntry[]>(`/log/recent?limit=${limit}`)
}

export function fetchOverview() {
  return apiFetch<OverviewStats>('/stats/overview')
}

export function fetchByCountry() {
  return apiFetch<CountryStat[]>('/stats/by-country')
}

export function fetchTimeline() {
  return apiFetch<TimelinePoint[]>('/stats/timeline')
}

export function fetchCellar() {
  return apiFetch<CellarItem[]>('/cellar')
}

export function updateCellar(id: number, data: Record<string, unknown>) {
  return apiFetch<CellarItem>(`/cellar/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deleteCellar(id: number) {
  return apiFetch(`/cellar/${id}`, { method: 'DELETE' })
}

export function fetchWishlist() {
  return apiFetch<WishlistItem[]>('/wishlist')
}

export function updateWishlist(id: number, data: Record<string, unknown>) {
  return apiFetch<WishlistItem>(`/wishlist/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export function deleteWishlist(id: number) {
  return apiFetch(`/wishlist/${id}`, { method: 'DELETE' })
}
