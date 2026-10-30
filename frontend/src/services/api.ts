/**
 * API Service — Backend ile iletişim.
 * lib/api.js'nin temizlenmiş / genişletilmiş hali.
 */
import { auth } from './auth'

export const API_BASE: string = import.meta.env.VITE_API_URL || ''

if (!API_BASE && import.meta.env.PROD) {
  console.error('UniSense: VITE_API_URL tanımlı değil! API çağrıları kendi origin\'ine gidecek.')
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function authHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (auth?.currentUser) {
    try {
      const token = await auth.currentUser.getIdToken()
      headers['Authorization'] = `Bearer ${token}`
    } catch { /* token alınamazsa anonim dene */ }
  }
  return headers
}

export async function apiFetch(path: string, options: { method?: string; body?: unknown; signal?: AbortSignal; timeout?: number } = {}): Promise<any> {
  const { method = 'GET', body, signal, timeout = 30000 } = options
  const controller = new AbortController()
  const id = setTimeout(() => controller.abort(), timeout)
  const finalSignal = signal ? AbortSignal.any([signal, controller.signal]) : controller.signal

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method, headers: await authHeaders(),
      body: body !== undefined ? JSON.stringify(body) : undefined, signal: finalSignal,
    })
    clearTimeout(id)

    if (res.status === 401) throw new ApiError('Bu özellik için giriş yapmalısın.', 401)
    if (res.status === 429) throw new ApiError('Çok fazla istek gönderildi — biraz bekleyip tekrar dene.', 429)
    if (!res.ok) throw new ApiError(`API ${res.status} — backend çalışıyor mu? (${API_BASE || 'localhost:8002'})`, res.status)
    return res.json()
  } catch (e: any) {
    clearTimeout(id)
    if (e.name === 'AbortError') throw new ApiError('İstek zaman aşımına uğradı.', 408)
    throw e
  }
}

// === Convenience methods ===
export const api = {
  health: () => apiFetch('/api/v1/health'),
  ask: (query: string, options: Record<string, unknown> = {}) => apiFetch('/api/v1/ask', {
    method: 'POST', body: { query, top_k: 12, ...options },
  }),
  recommend: (payload: unknown) => apiFetch('/api/v1/recommend', { method: 'POST', body: payload }),
  programsSearch: (params: unknown) => apiFetch('/api/v1/programs/search', { method: 'POST', body: params }),
  programsLookup: (codes: string[]) => apiFetch('/api/v1/programs/lookup', { method: 'POST', body: { codes } }),
  programsDetail: (code: string) => apiFetch(`/api/v1/programs/${code}`),
  dgsPrograms: (params: unknown) => apiFetch('/api/v1/dgs/programlar', { method: 'POST', body: params }),
  dgsGecis: (onlisans: unknown) => apiFetch('/api/v1/dgs/gecis', { method: 'POST', body: { onlisans } }),
  kpssKadrolar: (params: unknown) => apiFetch('/api/v1/kpss/kadrolar', { method: 'POST', body: params }),
  tusPrograms: (params: unknown) => apiFetch('/api/v1/tus/programlar', { method: 'POST', body: params }),
  lgsLiseler: (params: unknown) => apiFetch('/api/v1/lgs/liseler', { method: 'POST', body: params }),
  konular: (sinav: string) => apiFetch(`/api/v1/konular?sinav=${sinav}`),
  takvim: () => apiFetch('/api/v1/takvim'),
  scholarshipList: (params: Record<string, unknown> = {}) => {
    const qs = new URLSearchParams()
    if (params.year) qs.set('year', String(params.year))
    if (params.university) qs.set('university', String(params.university))
    if (params.department) qs.set('department', String(params.department))
    if (params.type) qs.set('type_filter', String(params.type))
    return apiFetch(`/api/v1/scholarship/list?${qs.toString()}`)
  },
  scholarshipByProgram: (code: string) => apiFetch(`/api/v1/scholarship/program/${code}`),
  scholarshipYears: () => apiFetch('/api/v1/scholarship/years'),
  employmentList: (params: Record<string, unknown> = {}) => {
    const qs = new URLSearchParams()
    if (params.year) qs.set('year', String(params.year))
    if (params.department) qs.set('department', String(params.department))
    return apiFetch(`/api/v1/employment/list?${qs.toString()}`)
  },
  employmentByProgram: (code: string) => apiFetch(`/api/v1/employment/program/${code}`),
  employmentYears: () => apiFetch('/api/v1/employment/years'),
  analyticsLog: (event_type: string, page?: string, user_id?: string | null) => apiFetch('/api/v1/analytics/log', {
    method: 'POST', body: { event_type, page, user_id },
  }),
  analyticsSummary: () => apiFetch('/api/v1/analytics/summary'),
  analyticsClear: () => apiFetch('/api/v1/analytics/clear', { method: 'DELETE' }),
  // Push notifications (backend endpoints - require Firebase Admin SDK)
  pushSend: () => apiFetch('/api/v1/push/send', { method: 'POST' }),
  pushExamReminder: () => apiFetch('/api/v1/push/exam-reminder', { method: 'POST' }),
  pushStreakReminder: () => apiFetch('/api/v1/push/streak-reminder', { method: 'POST' }),
  checkout: (payload: unknown) => apiFetch('/api/v1/billing/checkout', { method: 'POST', body: payload }),
  webhook: (payload: unknown) => apiFetch('/api/v1/billing/webhook', { method: 'POST', body: payload }),
  userProfile: () => apiFetch('/api/v1/user/profile'),
  userUpdate: (data: unknown) => apiFetch('/api/v1/user/profile', { method: 'POST', body: data }),
}

export default api