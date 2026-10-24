/**
 * Firestore Preferences Service — tüm sınav türleri için tercih listeleri.
 * Jenerik _watchTercih / _addToTercih / _removeFromTercih / _reorderTercih pattern'i.
 */
import { FIRESTORE_COLLECTIONS, TERCIH_LIMITS } from './constants'
import { db, query, orderBy, limit as fbLimit, onSnapshot, collection, doc, writeBatch, setDoc, serverTimestamp, deleteDoc, updateDoc } from './firestore-core'

// === Jeneric Tercih Helpers ===

function _watchTercih(uid, sub, maxLimit, callback) {
  if (!db) return () => {}
  const constraints = [orderBy('order', 'asc')]
  if (maxLimit) constraints.push(fbLimit(maxLimit))
  const q = query(collection(db, 'users', uid, sub), ...constraints)
  return onSnapshot(q, (snap) => callback(snap.docs.map(d => ({ id: d.id, ...d.data() }))))
}

async function _addToTercih(uid, sub, item, order, codeKey, dataMapper) {
  if (!db) throw new Error('Firestore yok')
  const code = String(item[codeKey] || item.code)
  await setDoc(doc(db, 'users', uid, sub, code), { ...dataMapper(item), [codeKey]: code, order, addedAt: serverTimestamp() })
}

async function _removeFromTercih(uid, sub, code) {
  if (!db) throw new Error('Firestore yok')
  await deleteDoc(doc(db, 'users', uid, sub, String(code)))
}

async function _reorderTercih(uid, sub, orderedItems) {
  if (!db) throw new Error('Firestore yok')
  if (!Array.isArray(orderedItems) || orderedItems.length === 0) return
  const batch = writeBatch(db)
  orderedItems.forEach((item, idx) => {
    const ref = doc(db, 'users', uid, sub, String(item.id || item.kod || item.code || item.kadro_kodu))
    batch.update(ref, { order: idx + 1 })
  })
  await batch.commit()
}

// === YKS Tercih Listesi (tercih) — max 24 ===

export function watchTercihList(uid, callback) {
  return _watchTercih(uid, FIRESTORE_COLLECTIONS.TERCIH, TERCIH_LIMITS.YKS, callback)
}

export async function addToTercih(uid, dept, order) {
  return _addToTercih(uid, FIRESTORE_COLLECTIONS.TERCIH, dept, order, 'department_code', (d) => ({
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

export async function removeFromTercih(uid, code) {
  return _removeFromTercih(uid, FIRESTORE_COLLECTIONS.TERCIH, code)
}

export async function updateTercihNote(uid, code, note) {
  if (!db) throw new Error('Firestore yok')
  const trimmed = (note || '').slice(0, 500)
  await updateDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.TERCIH, String(code)), {
    note: trimmed, noteUpdatedAt: serverTimestamp(),
  })
}

export async function reorderTercihList(uid, orderedItems) {
  return _reorderTercih(uid, FIRESTORE_COLLECTIONS.TERCIH, orderedItems)
}

export async function backfillTercihList(uid, codeToData) {
  if (!db) throw new Error('Firestore yok')
  if (!codeToData || Object.keys(codeToData).length === 0) return
  const batch = writeBatch(db)
  for (const [code, data] of Object.entries(codeToData)) {
    const ref = doc(db, 'users', uid, FIRESTORE_COLLECTIONS.TERCIH, String(code))
    const patch = {}
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

export function watchKpssTercih(uid, callback) {
  return _watchTercih(uid, FIRESTORE_COLLECTIONS.KPSS_TERCIH, TERCIH_LIMITS.KPSS, callback)
}

export async function addToKpssTercih(uid, kadro, order) {
  return _addToTercih(uid, FIRESTORE_COLLECTIONS.KPSS_TERCIH, kadro, order, 'kadro_kodu', (k) => ({
    kurum: k.kurum || '', unvan: k.unvan || '', il: k.il || '', duzey: k.duzey || '',
    puan_turu: k.puan_turu || '', kontenjan: k.kontenjan ?? null,
    gecmis_taban: k.gecmis_taban ?? null, eslesme: k.eslesme || '',
    ozel_kosullar: Array.isArray(k.ozel_kosullar) ? k.ozel_kosullar.slice(0, 3) : [],
  }))
}

export const removeFromKpssTercih = (uid, code) => _removeFromTercih(uid, FIRESTORE_COLLECTIONS.KPSS_TERCIH, code)
export const reorderKpssTercih = (uid, orderedItems) => _reorderTercih(uid, FIRESTORE_COLLECTIONS.KPSS_TERCIH, orderedItems)

// === DGS Tercih Listesi (dgs_tercih) — max 30 ===

export function watchDgsTercih(uid, callback) {
  return _watchTercih(uid, FIRESTORE_COLLECTIONS.DGS_TERCIH, TERCIH_LIMITS.DGS, callback)
}

export async function addToDgsTercih(uid, prog, order) {
  return _addToTercih(uid, FIRESTORE_COLLECTIONS.DGS_TERCIH, prog, order, 'department_code', (p) => ({
    program_adi: p.program_adi || '', university_name: p.university_name || '',
    city: p.city || '', puan_turu: p.puan_turu || '',
    kontenjan: p.kontenjan ?? null, min_puan: p.min_puan ?? null,
  }))
}

export const removeFromDgsTercih = (uid, code) => _removeFromTercih(uid, FIRESTORE_COLLECTIONS.DGS_TERCIH, code)
export const reorderDgsTercih = (uid, orderedItems) => _reorderTercih(uid, FIRESTORE_COLLECTIONS.DGS_TERCIH, orderedItems)

// === TUS/DUS Uzmanlık Tercih Listesi (tus_tercih / dus_tercih) — max 30 ===

const MAX_TUS_TERCIH = TERCIH_LIMITS.TUS
const _uzmanlikSub = (sinav) => (sinav === 'DUS' ? FIRESTORE_COLLECTIONS.DUS_TERCIH : FIRESTORE_COLLECTIONS.TUS_TERCIH)

export function watchUzmanlikTercih(uid, sinav, callback) {
  return _watchTercih(uid, _uzmanlikSub(sinav), MAX_TUS_TERCIH, callback)
}

export async function addToUzmanlikTercih(uid, sinav, prog, order) {
  return _addToTercih(uid, _uzmanlikSub(sinav), prog, order, 'kod', (p) => ({
    dal: p.dal || '', kurum: p.kurum || '', kontenjan_turu: p.kontenjan_turu || '',
    min_puan: p.min_puan ?? null, max_puan: p.max_puan ?? null,
    kontenjan: p.kontenjan ?? null, yerlesen: p.yerlesen ?? null,
  }))
}

export const removeFromUzmanlikTercih = (uid, sinav, code) => _removeFromTercih(uid, _uzmanlikSub(sinav), code)
export const reorderUzmanlikTercih = (uid, sinav, orderedItems) => _reorderTercih(uid, _uzmanlikSub(sinav), orderedItems)

// === LGS Lise Tercih Listesi (lgs_tercih) — max 25 ===

export function lgsTercihKey(lise) {
  const raw = `${lise.okul || ''}-${lise.ilce || ''}-${lise.dil || ''}-${lise.yuzdelik ?? ''}`
  return raw.replace(/İ/g, 'i').replace(/I/g, 'i').toLowerCase()
    .replace(/[çğıöşü]/g, c => ({ ç: 'c', ğ: 'g', ı: 'i', ö: 'o', ş: 's', ü: 'u' }[c] || c))
    .replace(/[^a-z0-9.]+/g, '-').replace(/^-|-$/g, '').slice(0, 200) || 'lise'
}

export function watchLgsTercih(uid, callback) {
  return _watchTercih(uid, FIRESTORE_COLLECTIONS.LGS_TERCIH, TERCIH_LIMITS.LGS, callback)
}

export async function addToLgsTercih(uid, lise, order) {
  return _addToTercih(uid, FIRESTORE_COLLECTIONS.LGS_TERCIH, lise, order, 'okul', (l) => ({
    il: l.il || '', ilce: l.ilce || '', tur: l.tur || '', dil: l.dil || '',
    yuzdelik: l.yuzdelik ?? null, taban_puan: l.taban_puan ?? null, kontenjan: l.kontenjan ?? null,
  }))
}

export const removeFromLgsTercih = (uid, key) => _removeFromTercih(uid, FIRESTORE_COLLECTIONS.LGS_TERCIH, key)
export const reorderLgsTercih = (uid, orderedItems) => _reorderTercih(uid, FIRESTORE_COLLECTIONS.LGS_TERCIH, orderedItems)

// === Jeneric reorder for other subcollections ===

export async function reorderSubcollection(uid, sub, orderedIds) {
  return _reorderTercih(uid, sub, orderedIds)
}