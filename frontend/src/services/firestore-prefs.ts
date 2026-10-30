/**
 * Firestore Preferences Service — tüm sınav türleri için tercih listeleri.
 * Jenerik _watchTercih / _addToTercih / _removeFromTercih / _reorderTercih pattern'i.
 */
import { FIRESTORE_COLLECTIONS, TERCIH_LIMITS } from './constants'
import { db, query, orderBy, limit as fbLimit, onSnapshot, collection, doc, writeBatch, setDoc, serverTimestamp, deleteDoc, updateDoc } from './firestore-core'

// === Jeneric Tercih Helpers ===

function _watchTercih(uid: string, sub: string, maxLimit: number | null, callback: (items: any[]) => void): () => void {
  if (!db) return () => {}
  const constraints: any[] = [orderBy('order', 'asc')]
  if (maxLimit) constraints.push(fbLimit(maxLimit))
  const q = query(collection(db, 'users', uid, sub), ...constraints)
  return onSnapshot(q, (snap: any) => callback(snap.docs.map((d: any) => ({ id: d.id, ...d.data() }))))
}

async function _addToTercih(uid: string, sub: string, item: any, order: number, codeKey: string, dataMapper: (item: any) => any): Promise<void> {
  if (!db) throw new Error('Firestore yok')
  const code = String(item[codeKey] || item.code)
  await setDoc(doc(db, 'users', uid, sub, code), { ...dataMapper(item), [codeKey]: code, order, addedAt: serverTimestamp() })
}

async function _removeFromTercih(uid: string, sub: string, code: string | number): Promise<void> {
  if (!db) throw new Error('Firestore yok')
  await deleteDoc(doc(db, 'users', uid, sub, String(code)))
}

async function _reorderTercih(uid: string, sub: string, orderedItems: any[]): Promise<void> {
  if (!db) throw new Error('Firestore yok')
  if (!Array.isArray(orderedItems) || orderedItems.length === 0) return
  const batch = writeBatch(db)
  orderedItems.forEach((item: any, idx: number) => {
    const ref = doc(db!, 'users', uid, sub, String(item.id || item.kod || item.code || item.kadro_kodu))
    batch.update(ref, { order: idx + 1 })
  })
  await batch.commit()
}

// === YKS TERCİH LİSTESİ (tercih) — max 24 ===

export function watchTercihList(uid: string, callback: (items: any[]) => void): () => void {
  return _watchTercih(uid, 'tercih', TERCIH_LIMITS.YKS, callback)
}

export async function addToTercih(uid: string, dept: any, order: number): Promise<void> {
  return _addToTercih(uid, 'tercih', dept, order, 'department_code', (d: any) => ({
    department_name: d.department_name || d.name,
    university_code: d.university_code,
    university_name: d.university_name || d.universityName,
    city: d.city || '',
    score_type: d.score_type || d.scoreType || null,
    last_year_base_rank: d.last_year_base_rank ?? null,
    last_year_base_score: d.last_year_base_score ?? null,
    quota: d.quota ?? null,
    fit_score: d.fit_score ?? null,
    safety_level: d.safety_level || null,
  }))
}

export async function removeFromTercih(uid: string, code: string | number): Promise<void> {
  return _removeFromTercih(uid, 'tercih', code)
}

export async function updateTercihNote(uid: string, code: string | number, note: string): Promise<void> {
  if (!db) throw new Error('Firestore yok')
  const trimmed = (note || '').slice(0, 500)
  await updateDoc(doc(db, 'users', uid, 'tercih', String(code)), {
    note: trimmed, noteUpdatedAt: serverTimestamp(),
  })
}

export async function reorderTercihList(uid: string, orderedItems: any[]): Promise<void> {
  return _reorderTercih(uid, 'tercih', orderedItems)
}

export async function backfillTercihList(uid: string, codeToData: Record<string, any>): Promise<void> {
  if (!db) throw new Error('Firestore yok')
  if (!codeToData || Object.keys(codeToData).length === 0) return
  const batch = writeBatch(db)
  for (const [code, data] of Object.entries(codeToData)) {
    const ref = doc(db, 'users', uid, 'tercih', String(code))
    const patch: any = {}
    if (data.last_year_base_rank != null) patch.last_year_base_rank = data.last_year_base_rank
    if (data.last_year_base_score != null) patch.last_year_base_score = data.last_year_base_score
    if (data.quota != null) patch.quota = data.quota
    if (data.score_type) patch.score_type = data.score_type
    if (data.city) patch.city = data.city
    if (data.university_name) patch.university_name = data.university_name
    if (data.department_name) patch.department_name = data.department_name
    if (Object.keys(patch).length > 0) batch.update(ref, patch)
  }
  await batch.commit()
}

// === KPSS Tercih Listesi (kpss_tercih) — max 30 ===

export const MAX_KPSS_TERCIH = 30

export function watchKpssTercih(uid: string, callback: (items: any[]) => void): () => void {
  return _watchTercih(uid, 'kpss_tercih', MAX_KPSS_TERCIH, callback)
}

export async function addToKpssTercih(uid: string, kadro: any, order: number): Promise<void> {
  return _addToTercih(uid, 'kpss_tercih', kadro, order, 'kadro_kodu', (k: any) => ({
    kurum: k.kurum || '',
    unvan: k.unvan || '',
    il: k.il || '',
    duzey: k.duzey || '',
    puan_turu: k.puan_turu || '',
    kontenjan: k.kontenjan ?? null,
    gecmis_taban: k.gecmis_taban ?? null,
    eslesme: k.eslesme || '',
    ozel_kosullar: Array.isArray(k.ozel_kosullar) ? k.ozel_kosullar.slice(0, 3) : [],
  }))
}

export const removeFromKpssTercih = (uid: string, code: string | number) => _removeFromTercih(uid, 'kpss_tercih', code)
export const reorderKpssTercih = (uid: string, orderedItems: any[]) => _reorderTercih(uid, 'kpss_tercih', orderedItems)

// === DGS Tercih Listesi (dgs_tercih) — max 30 ===

export const MAX_DGS_TERCIH = 30

export function watchDgsTercih(uid: string, callback: (items: any[]) => void): () => void {
  return _watchTercih(uid, 'dgs_tercih', MAX_DGS_TERCIH, callback)
}

export async function addToDgsTercih(uid: string, prog: any, order: number): Promise<void> {
  return _addToTercih(uid, 'dgs_tercih', prog, order, 'department_code', (p: any) => ({
    program_adi: p.program_adi || '',
    university_name: p.university_name || '',
    city: p.city || '',
    puan_turu: p.puan_turu || '',
    kontenjan: p.kontenjan ?? null,
    min_puan: p.min_puan ?? null,
  }))
}

export const removeFromDgsTercih = (uid: string, code: string | number) => _removeFromTercih(uid, 'dgs_tercih', code)
export const reorderDgsTercih = (uid: string, orderedItems: any[]) => _reorderTercih(uid, 'dgs_tercih', orderedItems)

// === TUS/DUS Uzmanlık Tercih Listesi (tus_tercih / dus_tercih) — max 30 ===

export const MAX_TUS_TERCIH = 30

const _uzmanlikSub = (sinav: string) => (sinav === 'DUS' ? 'dus_tercih' : 'tus_tercih')

export function watchUzmanlikTercih(uid: string, sinav: string, callback: (items: any[]) => void): () => void {
  return _watchTercih(uid, _uzmanlikSub(sinav), MAX_TUS_TERCIH, callback)
}

export async function addToUzmanlikTercih(uid: string, sinav: string, prog: any, order: number): Promise<void> {
  return _addToTercih(uid, _uzmanlikSub(sinav), prog, order, 'kod', (p: any) => ({
    dal: p.dal || '',
    kurum: p.kurum || '',
    kontenjan_turu: p.kontenjan_turu || '',
    min_puan: p.min_puan ?? null,
    max_puan: p.max_puan ?? null,
    kontenjan: p.kontenjan ?? null,
    yerlesen: p.yerlesen ?? null,
  }))
}

export const removeFromUzmanlikTercih = (uid: string, sinav: string, code: string | number) => _removeFromTercih(uid, _uzmanlikSub(sinav), code)
export const reorderUzmanlikTercih = (uid: string, sinav: string, orderedItems: any[]) => _reorderTercih(uid, _uzmanlikSub(sinav), orderedItems)

// === LGS Lise Tercih Listesi (lgs_tercih) — max 25 ===

export const MAX_LGS_TERCIH = 25

export function lgsTercihKey(lise: any): string {
  const raw = `${lise.okul || ''}-${lise.ilce || ''}-${lise.dil || ''}-${lise.yuzdelik ?? ''}`
  return raw.replace(/İ/g, 'i').replace(/I/g, 'i').toLowerCase()
    .replace(/[çğıöşü]/g, (c: string) => ({ ç: 'c', ğ: 'g', ı: 'i', ö: 'o', ş: 's', ü: 'u' }[c] || c))
    .replace(/[^a-z0-9.]+/g, '-').replace(/^-|-$/g, '').slice(0, 200) || 'lise'
}

export function watchLgsTercih(uid: string, callback: (items: any[]) => void): () => void {
  return _watchTercih(uid, 'lgs_tercih', TERCIH_LIMITS.LGS, callback)
}

export async function addToLgsTercih(uid: string, lise: any, order: number): Promise<void> {
  return _addToTercih(uid, 'lgs_tercih', lise, order, 'okul', (l: any) => ({
    il: l.il || '',
    ilce: l.ilce || '',
    tur: l.tur || '',
    dil: l.dil || '',
    yuzdelik: l.yuzdelik ?? null,
    taban_puan: l.taban_puan ?? null,
    kontenjan: l.kontenjan ?? null,
  }))
}

export const removeFromLgsTercih = (uid: string, key: string | number) => _removeFromTercih(uid, 'lgs_tercih', key)
export const reorderLgsTercih = (uid: string, orderedItems: any[]) => _reorderTercih(uid, 'lgs_tercih', orderedItems)

// === Jeneric reorder for other subcollections ===

export async function reorderSubcollection(uid: string, sub: string, orderedIds: any[]): Promise<void> {
  return _reorderTercih(uid, sub, orderedIds)
}