/**
 * Backend API istemcisi.
 *
 * - VITE_API_URL yoksa production build'de görünür hata verir (sessizce
 *   kendi origin'ine 404 atmak yerine).
 * - Kullanıcı girişliyse her isteğe Firebase ID token ekler
 *   (backend SECURITY_REQUIRE_AUTH=true iken /ask ve /recommend bunu ister).
 * - 401/429 için kullanıcı-dostu Türkçe mesajlı ApiError fırlatır.
 */
import { auth } from '@/services/auth'

export const API_BASE = import.meta.env.VITE_API_URL || ''

if (!API_BASE && import.meta.env.PROD) {
  // Build'e sızmış konfigürasyon hatası — konsolda bağır
  console.error(
    'UniSense: VITE_API_URL tanımlı değil! API çağrıları kendi origin\'ine ' +
    'gidip 404 alacak. Vercel → Settings → Environment Variables kontrol et.'
  )
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
    } catch {
      // Token alınamazsa anonim dene — backend gerekiyorsa 401 döner
    }
  }
  return headers
}

/**
 * fetch sarmalayıcı — JSON body gönderir, JSON cevap döner.
 * @param {string} path - /api/v1/... yolu
 * @param {{method?: string, body?: any, signal?: AbortSignal}} [options]
 */
export async function apiFetch(path: string, { method = 'GET', body, signal }: { method?: string; body?: any; signal?: AbortSignal } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: await authHeaders(),
    body: body !== undefined ? JSON.stringify(body) : undefined,
    signal,
  })
  if (res.status === 401) {
    throw new ApiError('Bu özellik için giriş yapmalısın.', 401)
  }
  if (res.status === 429) {
    throw new ApiError('Çok fazla istek gönderildi — biraz bekleyip tekrar dene.', 429)
  }
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    let msg = `API ${res.status} — backend çalışıyor mu? (${API_BASE || 'localhost:8002'})`
    if (body && typeof body.detail === 'string' && body.detail.trim()) {
      msg = body.detail
    } else if (body && Array.isArray(body.detail) && body.detail.length > 0) {
      const joined = body.detail
        .map((d: any) => (d && typeof d.msg === 'string' ? d.msg : ''))
        .filter(Boolean)
        .join('; ')
      if (joined) msg = joined
    }
    throw new ApiError(msg, res.status)
  }
  return res.json()
}
