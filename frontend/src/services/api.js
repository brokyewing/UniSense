/**
 * API Service — Backend ile iletişim.
 * lib/api.js'nin temizlenmiş / genişletilmiş hali.
 */
import { auth } from '../firebase'

export const API_BASE = import.meta.env.VITE_API_URL || ''

if (!API_BASE && import.meta.env.PROD) {
  console.error('UniSense: VITE_API_URL tanımlı değil! API çağrıları kendi origin\'ine gidecek.')
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function authHeaders() {
  const headers = { 'Content-Type': 'application/json' }
  if (auth?.currentUser) {
    try {
      const token = await auth.currentUser.getIdToken()
      headers['Authorization'] = `Bearer ${token}`
    } catch { /* token alınamazsa anonim dene */ }
  }
  return headers
}

/**
 * Generic fetch wrapper
 * @param {string} path - /api/v1/... path
 * @param {Object} options - { method, body, signal, timeout }
 */
export async function apiFetch(path, { method = 'GET', body, signal, timeout = 30000 } = {}) {
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
  } catch (e) {
    clearTimeout(id)
    if (e.name === 'AbortError') throw new ApiError('İstek zaman aşımına uğradı.', 408)
    throw e
  }
}

// === Convenience methods ===

export const api = {
  // Health
  health: () => apiFetch('/api/v1/health'),

  // Ask / Chat
  ask: (query, options = {}) => apiFetch('/api/v1/ask', {
    method: 'POST', body: { query, top_k: 12, ...options },
  }),

  // Recommend
  recommend: (payload) => apiFetch('/api/v1/recommend', { method: 'POST', body: payload }),

  // Programs
  programsSearch: (params) => apiFetch('/api/v1/programs/search', { method: 'POST', body: params }),
  programsLookup: (codes) => apiFetch('/api/v1/programs/lookup', { method: 'POST', body: { codes } }),
  programsDetail: (code) => apiFetch(`/api/v1/programs/${code}`),

  // DGS
  dgsPrograms: (params) => apiFetch('/api/v1/dgs/programlar', { method: 'POST', body: params }),
  dgsGecis: (onlisans) => apiFetch('/api/v1/dgs/gecis', { method: 'POST', body: { onlisans } }),

  // KPSS
  kpssKadrolar: (params) => apiFetch('/api/v1/kpss/kadrolar', { method: 'POST', body: params }),

  // TUS/DUS
  tusPrograms: (params) => apiFetch('/api/v1/tus/programlar', { method: 'POST', body: params }),

  // LGS
  lgsLiseler: (params) => apiFetch('/api/v1/lgs/liseler', { method: 'POST', body: params }),

  // Konular
  konular: (sinav) => apiFetch(`/api/v1/konular?sinav=${sinav}`),

  // Billing / İyzico
  checkout: (payload) => apiFetch('/api/v1/billing/checkout', { method: 'POST', body: payload }),
  webhook: (payload) => apiFetch('/api/v1/billing/webhook', { method: 'POST', body: payload }),

  // User context endpoints (if any)
  userProfile: () => apiFetch('/api/v1/user/profile'),
  userUpdate: (data) => apiFetch('/api/v1/user/profile', { method: 'POST', body: data }),
}

export default api