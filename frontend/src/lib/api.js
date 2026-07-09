/**
 * Backend API istemcisi.
 *
 * - VITE_API_URL yoksa production build'de görünür hata verir (sessizce
 *   kendi origin'ine 404 atmak yerine).
 * - Kullanıcı girişliyse her isteğe Firebase ID token ekler
 *   (backend SECURITY_REQUIRE_AUTH=true iken /ask ve /recommend bunu ister).
 * - 401/429 için kullanıcı-dostu Türkçe mesajlı ApiError fırlatır.
 */
import { auth } from '../firebase'

export const API_BASE = import.meta.env.VITE_API_URL || ''

if (!API_BASE && import.meta.env.PROD) {
  // Build'e sızmış konfigürasyon hatası — konsolda bağır
  console.error(
    'UniSense: VITE_API_URL tanımlı değil! API çağrıları kendi origin\'ine ' +
    'gidip 404 alacak. Vercel → Settings → Environment Variables kontrol et.'
  )
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
export async function apiFetch(path, { method = 'GET', body, signal } = {}) {
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
    throw new ApiError(`API ${res.status} — backend çalışıyor mu? (${API_BASE || 'localhost:8002'})`, res.status)
  }
  return res.json()
}
