/**
 * Misafir (girişsiz) YKS tercih taslağı — localStorage kalıcılığı (max 24).
 * Giriş yapıldığında TercihList tarafından Firestore'a otomatik aktarılır.
 */
const GUEST_TERCIH_KEY = 'unisense_guest_tercih_yks'
const MAX_YKS = 24

export function markEngaged(): void {
  try {
    localStorage.setItem('unisense_engaged', '1')
    window.dispatchEvent(new Event('unisense:engaged'))
  } catch { /* noop */ }
}

export function getGuestTercih(): any[] {
  try {
    const raw = localStorage.getItem(GUEST_TERCIH_KEY)
    const parsed = raw ? JSON.parse(raw) : []
    return Array.isArray(parsed) ? parsed.slice(0, MAX_YKS) : []
  } catch {
    return []
  }
}

export function setGuestTercih(items: any[]): void {
  try {
    localStorage.setItem(GUEST_TERCIH_KEY, JSON.stringify((items || []).slice(0, MAX_YKS)))
    window.dispatchEvent(new Event('unisense:guest-tercih'))
  } catch { /* noop */ }
}

export function addGuestTercih(item: any): { ok: boolean; error?: string; items: any[] } {
  const cur = getGuestTercih()
  const code = String(item.department_code || item.id || '')
  if (!code) return { ok: false, error: 'Geçersiz program kodu', items: cur }
  if (cur.some((x) => String(x.department_code || x.id) === code)) {
    return { ok: true, items: cur }
  }
  if (cur.length >= MAX_YKS) {
    return { ok: false, error: `Tercih listesi ${MAX_YKS} dolu`, items: cur }
  }
  const entry = {
    id: code,
    department_code: code,
    department_name: item.department_name || item.name || '',
    university_code: item.university_code || '',
    university_name: item.university_name || item.universityName || '',
    city: item.city || '',
    score_type: item.score_type || item.scoreType || null,
    last_year_base_rank: item.last_year_base_rank ?? null,
    last_year_base_score: item.last_year_base_score ?? null,
    quota: item.quota ?? null,
    fit_score: item.fit_score ?? null,
    safety_level: item.safety_level || null,
    order: cur.length + 1,
  }
  const next = [...cur, entry]
  setGuestTercih(next)
  markEngaged()
  return { ok: true, items: next }
}

export function removeGuestTercih(code: string | number): any[] {
  const c = String(code)
  const next = getGuestTercih()
    .filter((x) => String(x.department_code || x.id) !== c)
    .map((x, idx) => ({ ...x, order: idx + 1 }))
  setGuestTercih(next)
  return next
}

export function clearGuestTercih(): void {
  try {
    localStorage.removeItem(GUEST_TERCIH_KEY)
    window.dispatchEvent(new Event('unisense:guest-tercih'))
  } catch { /* noop */ }
}
