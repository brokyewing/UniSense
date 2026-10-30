/**
 * Firestore Plan & Stats Service — planlayıcı, istatistik, streak, sıralama.
 */
import { FIRESTORE_COLLECTIONS } from './constants'
import { db, collection, doc, query, where, orderBy, limit as fbLimit, onSnapshot, getDoc, getDocs, setDoc, updateDoc, deleteDoc, writeBatch, increment, serverTimestamp, deleteField, getCountFromServer } from './firestore-core'
import { serisiIsle, bugunStr, guncelSeri } from '../lib/streak'

// === Planlayıcı ===

export async function getPlanConfig(uid: string): Promise<any> {
  if (!db || !uid) return null
  try { const s = await getDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_CONFIG, 'genel')); return s.exists() ? s.data() : null } catch { return null }
}

export async function setPlanConfig(uid: string, cfg: any): Promise<void> {
  if (!db || !uid) return
  await setDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_CONFIG, 'genel'), { ...cfg, updatedAt: serverTimestamp() }, { merge: true })
}

export function watchPlanGorevler(uid: string, hafta: string, callback: (data: any) => void): () => void {
  if (!db) return () => {}
  const q = query(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_GOREV), where('hafta', '==', hafta))
  return onSnapshot(q, (snap: any) => callback(snap.docs.map((d: any) => ({ id: d.id, ...d.data() }))), () => callback(null))
}

export async function addPlanGorev(uid: string, task: any): Promise<string | null> {
  if (!db) return null
  const { id, ...rest } = task
  const ref = await addDoc(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_GOREV), { ...rest, createdAt: serverTimestamp() })
  return ref.id
}

export async function addPlanGorevler(uid: string, tasks: any[]): Promise<void> {
  if (!db || !uid || !tasks.length) return
  const batch = writeBatch(db)
  for (const t of tasks) {
    const { id, ...rest } = t
    batch.set(doc(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_GOREV)), { ...rest, createdAt: serverTimestamp() })
  }
  await batch.commit()
}

export async function updatePlanGorev(uid: string, id: string, patch: any): Promise<void> {
  if (!db || !uid || !id) return
  await updateDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_GOREV, id), patch)
}

export async function removePlanGorev(uid: string, id: string): Promise<void> {
  if (!db || !uid || !id) return
  await deleteDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_GOREV, id))
}

export async function getKonuChecked(uid: string, sinav: string): Promise<any> {
  if (!db || !uid) return {}
  try { const s = await getDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.KONU_ILERLEME, sinav)); return s.exists() ? (s.data().checked || {}) : {} } catch { return {} }
}

export async function getSoruList(uid: string, sinav: string): Promise<any[]> {
  if (!db || !uid) return []
  try { const snap = await getDocs(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SORU_KAYIT)); return snap.docs.map((d: any) => d.data()).filter((r: any) => !sinav || r.sinav === sinav) } catch { return [] }
}

// === İstatistik Toplama ===

export async function getIstatistik(uid: string): Promise<any> {
  const s: any = { konuDone: 0, denemeSayisi: 0, soruCozulen: 0, yanlisSayisi: 0, streakLongest: 0, sureDk: 0, sureHafta: {}, dersSure: {}, kullanimDk: 0, dogruCevap: 0, planGorev: 0 }
  if (!db || !uid) return s
  try {
    const [konu, den, soru, yan, akt, ist, plan] = await Promise.all([
      getDocs(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.KONU_ILERLEME)),
      getDocs(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.DENEMELER)),
      getDocs(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SORU_KAYIT)),
      getDocs(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.YANLISLAR)),
      getDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.AKTIVITE, 'gunluk')),
      getDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.ISTATISTIK, 'genel')),
      getDocs(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_GOREV)),
    ])
    konu.forEach((d: any) => { s.konuDone += Object.keys(d.data().checked || {}).length })
    s.denemeSayisi = den.size
    soru.forEach((d: any) => { s.soruCozulen += d.data().cozulen || 0 })
    s.yanlisSayisi = yan.size
    plan.forEach((d: any) => { if (d.data().status === 'done') s.planGorev += 1 })
    if (akt.exists()) s.streakLongest = akt.data().longest || 0
    if (ist.exists()) { const g = ist.data(); s.sureDk = g.sureDk || 0; s.sureHafta = g.sureHafta || {}; s.dersSure = g.dersSure || {}; s.kullanimDk = g.kullanimDk || 0; s.dogruCevap = g.dogruCevap || 0 }
    // Budama
    const ref = doc(db, 'users', uid, FIRESTORE_COLLECTIONS.ISTATISTIK, 'genel')
    const budamalar: any = {}
    const gunler = Object.keys(s.sureHafta)
    if (gunler.length > 60) { const tut = new Set(gunler.sort().slice(-30)); for (const g of gunler) if (!tut.has(g)) { budamalar[`sureHafta.${g}`] = deleteField(); delete s.sureHafta[g] } }
    const dersler = Object.keys(s.dersSure)
    if (dersler.length > 40) { const tut = new Set(dersler.sort((a: string, b: string) => (s.dersSure[b] || 0) - (s.dersSure[a] || 0)).slice(0, 30)); for (const d2 of dersler) if (!tut.has(d2)) { budamalar[`dersSure.${d2}`] = deleteField(); delete s.dersSure[d2] } }
    if (Object.keys(budamalar).length) updateDoc(ref, budamalar).catch(() => {})
  } catch { /* erişilemedi */ }
  return s
}

// === Sıralama (top-level collection) ===

export async function siralamaBenim(uid: string): Promise<any> {
  if (!db || !uid) return null
  try { const snap = await getDoc(doc(db, FIRESTORE_COLLECTIONS.SIRALAMA, uid)); return snap.exists() ? snap.data() : null } catch { return null }
}

export async function siralamaKaydet(uid: string, ad: string, seviye: number, xp: number): Promise<string> {
  if (!db) throw new Error('Firestore yok')
  const temizAd = String(ad || '').replace(/\s+/g, ' ').trim().slice(0, 24)
  if (temizAd.length < 2) throw new Error('Takma ad en az 2 karakter olmalı')
  await setDoc(doc(db, FIRESTORE_COLLECTIONS.SIRALAMA, uid), {
    ad: temizAd, seviye: Math.max(1, Math.min(500, Math.floor(seviye || 1))), xp: Math.max(0, Math.min(100000000, Math.floor(xp || 0))), guncel: serverTimestamp(),
  })
  return temizAd
}

export async function siralamaCik(uid: string): Promise<void> {
  if (!db) throw new Error('Firestore yok')
  await deleteDoc(doc(db, FIRESTORE_COLLECTIONS.SIRALAMA, uid))
}

export async function siralamaListe(n: number = 100): Promise<any[]> {
  if (!db) return []
  try { const snap = await getDocs(query(collection(db, FIRESTORE_COLLECTIONS.SIRALAMA), orderBy('xp', 'desc'), fbLimit(n))); return snap.docs.map((d: any) => ({ uid: d.id, ...d.data() })) } catch { return [] }
}

export async function siralamaSira(xp: number): Promise<number | null> {
  if (!db) return null
  try { const snap = await getCountFromServer(query(collection(db, FIRESTORE_COLLECTIONS.SIRALAMA), where('xp', '>', Math.floor(xp || 0)))); return snap.data().count + 1 } catch { return null }
}

// === Streak ===

export async function getStreak(uid: string): Promise<any> {
  const { getDoc, doc } = await import('./firestore-core')
  let s: any = null
  if (uid && db) {
    try { const snap = await getDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.AKTIVITE, 'gunluk')); if (snap.exists()) s = snap.data() } catch { /* noop */ }
  }
  return { current: guncelSeri(s), longest: s?.longest || 0 }
}

export async function recordActivity(uid: string | null): Promise<number> {
  const today = bugunStr()
  if (localStorage.getItem('unisense_streak_last') === today) return guncelSeri(JSON.parse(localStorage.getItem('unisense_streak') || 'null'))
  let prev: any = null
  if (uid && db) { try { const snap = await getDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.AKTIVITE, 'gunluk')); if (snap.exists()) prev = snap.data() } catch { /* noop */ } }
  const next = serisiIsle(prev, today)
  localStorage.setItem('unisense_streak', JSON.stringify(next))
  localStorage.setItem('unisense_streak_last', today)
  if (uid && db && next.changed) {
    setDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.AKTIVITE, 'gunluk'), { current: next.current, longest: next.longest, lastDate: next.lastDate, updatedAt: serverTimestamp() }, { merge: true }).catch(() => {})
  }
  return next.current
}

// === Pomodoro / Sure ===

export async function sureEkle(uid: string, dk: number, ders: string): Promise<void> {
  if (!db || !uid || !dk) return
  const today = bugunStr()
  const patch: any = { sureDk: increment(dk), sureHafta: { [today]: increment(dk) }, updatedAt: serverTimestamp() }
  if (ders) patch.dersSure = { [ders]: increment(dk) }
  await setDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.ISTATISTIK, 'genel'), patch, { merge: true }).catch(() => {})
}

export function guestStats(): any {
  let s: any = { konuDone: 0, denemeSayisi: 0, soruCozulen: 0, yanlisSayisi: 0, streakLongest: 0, sureDk: 0, sureHafta: {}, dersSure: {}, kullanimDk: 0, dogruCevap: 0, planGorev: 0 }
  try { const local = JSON.parse(localStorage.getItem('unisense_sure') || '{}'); s.sureDk = local.sureDk || 0; s.sureHafta = local.sureHafta || {}; s.dersSure = local.dersSure || {} } catch { /* noop */ }
  return s
}