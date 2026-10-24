/**
 * Firestore Plan & Stats Service — planlayıcı, istatistik, streak, sıralama.
 */
import { FIRESTORE_COLLECTIONS, MAX_SESSIONS_PER_USER } from './constants'
import { db, collection, doc, query, where, orderBy, limit as fbLimit, onSnapshot, getDoc, getDocs, setDoc, updateDoc, deleteDoc, writeBatch, increment, serverTimestamp, deleteField, getCountFromServer } from './firestore-core'
import { serisiIsle, bugunStr, guncelSeri } from '../lib/streak'

// === Planlayıcı ===

export async function getPlanConfig(uid) {
  if (!db || !uid) return null
  try { const s = await getDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_CONFIG, 'genel')); return s.exists() ? s.data() : null } catch { return null }
}

export async function setPlanConfig(uid, cfg) {
  if (!db || !uid) return
  await setDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_CONFIG, 'genel'), { ...cfg, updatedAt: serverTimestamp() }, { merge: true })
}

export function watchPlanGorevler(uid, hafta, callback) {
  if (!db) return () => {}
  const q = query(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_GOREV), where('hafta', '==', hafta))
  return onSnapshot(q, (snap) => callback(snap.docs.map(d => ({ id: d.id, ...d.data() }))), () => callback(null))
}

export async function addPlanGorev(uid, task) {
  const { id, ...rest } = task
  const ref = await addDoc(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_GOREV), { ...rest, createdAt: serverTimestamp() })
  return ref.id
}

export async function addPlanGorevler(uid, tasks) {
  if (!db || !uid || !tasks.length) return
  const batch = writeBatch(db)
  for (const t of tasks) {
    const { id, ...rest } = t
    batch.set(doc(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_GOREV)), { ...rest, createdAt: serverTimestamp() })
  }
  await batch.commit()
}

export async function updatePlanGorev(uid, id, patch) {
  if (!db || !uid || !id) return
  await updateDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_GOREV, id), patch)
}

export async function removePlanGorev(uid, id) {
  if (!db || !uid || !id) return
  await deleteDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.PLAN_GOREV, id))
}

export async function getKonuChecked(uid, sinav) {
  if (!db || !uid) return {}
  try { const s = await getDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.KONU_ILERLEME, sinav)); return s.exists() ? (s.data().checked || {}) : {} } catch { return {} }
}

export async function getSoruList(uid, sinav) {
  if (!db || !uid) return []
  try { const snap = await getDocs(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SORU_KAYIT)); return snap.docs.map(d => d.data()).filter(r => !sinav || r.sinav === sinav) } catch { return [] }
}

// === İstatistik Toplama ===

export async function getIstatistik(uid) {
  const s = { konuDone: 0, denemeSayisi: 0, soruCozulen: 0, yanlisSayisi: 0, streakLongest: 0, sureDk: 0, sureHafta: {}, dersSure: {}, kullanimDk: 0, dogruCevap: 0, planGorev: 0 }
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
    konu.forEach(d => { s.konuDone += Object.keys(d.data().checked || {}).length })
    s.denemeSayisi = den.size
    soru.forEach(d => { s.soruCozulen += d.data().cozulen || 0 })
    s.yanlisSayisi = yan.size
    plan.forEach(d => { if (d.data().status === 'done') s.planGorev += 1 })
    if (akt.exists()) s.streakLongest = akt.data().longest || 0
    if (ist.exists()) { const g = ist.data(); s.sureDk = g.sureDk || 0; s.sureHafta = g.sureHafta || {}; s.dersSure = g.dersSure || {}; s.kullanimDk = g.kullanimDk || 0; s.dogruCevap = g.dogruCevap || 0 }
    // Budama
    const ref = doc(db, 'users', uid, FIRESTORE_COLLECTIONS.ISTATISTIK, 'genel')
    const budamalar = {}
    const gunler = Object.keys(s.sureHafta)
    if (gunler.length > 60) { const tut = new Set(gunler.sort().slice(-30)); for (const g of gunler) if (!tut.has(g)) { budamalar[`sureHafta.${g}`] = deleteField(); delete s.sureHafta[g] } }
    const dersler = Object.keys(s.dersSure)
    if (dersler.length > 40) { const tut = new Set(dersler.sort((a, b) => (s.dersSure[b] || 0) - (s.dersSure[a] || 0)).slice(0, 30)); for (const d2 of dersler) if (!tut.has(d2)) { budamalar[`dersSure.${d2}`] = deleteField(); delete s.dersSure[d2] } }
    if (Object.keys(budamalar).length) updateDoc(ref, budamalar).catch(() => {})
  } catch { /* erişilemedi */ }
  return s
}

// === Sıralama (top-level collection) ===

export async function siralamaBenim(uid) {
  if (!db || !uid) return null
  try { const snap = await getDoc(doc(db, FIRESTORE_COLLECTIONS.SIRALAMA, uid)); return snap.exists() ? snap.data() : null } catch { return null }
}

export async function siralamaKaydet(uid, ad, seviye, xp) {
  if (!db) throw new Error('Firestore yok')
  const temizAd = String(ad || '').replace(/\s+/g, ' ').trim().slice(0, 24)
  if (temizAd.length < 2) throw new Error('Takma ad en az 2 karakter olmalı')
  await setDoc(doc(db, FIRESTORE_COLLECTIONS.SIRALAMA, uid), {
    ad: temizAd, seviye: Math.max(1, Math.min(500, Math.floor(seviye || 1))), xp: Math.max(0, Math.min(100000000, Math.floor(xp || 0))), guncel: serverTimestamp(),
  })
  return temizAd
}

export async function siralamaCik(uid) {
  if (!db) throw new Error('Firestore yok')
  await deleteDoc(doc(db, FIRESTORE_COLLECTIONS.SIRALAMA, uid))
}

export async function siralamaListe(n = 100) {
  if (!db) return []
  try { const snap = await getDocs(query(collection(db, FIRESTORE_COLLECTIONS.SIRALAMA), orderBy('xp', 'desc'), fbLimit(n))); return snap.docs.map(d => ({ uid: d.id, ...d.data() })) } catch { return [] }
}

export async function siralamaSira(xp) {
  if (!db) return null
  try { const snap = await getCountFromServer(query(collection(db, FIRESTORE_COLLECTIONS.SIRALAMA), where('xp', '>', Math.floor(xp || 0)))); return snap.data().count + 1 } catch { return null }
}

// === Streak (localStorage + bulut senkron) ===

const SK = 'unisense_streak'
const loadStreak = () => { try { return JSON.parse(localStorage.getItem(SK) || 'null') } catch { return null } }
const saveStreak = (s) => { try { localStorage.setItem(SK, JSON.stringify(s)) } catch {} }

export async function getStreak(uid) {
  let s = loadStreak()
  if (uid && db) { try { const snap = await getDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.AKTIVITE, 'gunluk')); if (snap.exists()) { s = snap.data(); saveStreak(s) } } catch {} }
  return { current: guncelSeri(s), longest: s?.longest || 0 }
}

export async function recordActivity(uid) {
  const today = bugunStr()
  if (localStorage.getItem(SK + '_last') === today) return guncelSeri(loadStreak())
  let prev = loadStreak()
  if (uid && db) { try { const snap = await getDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.AKTIVITE, 'gunluk')); if (snap.exists()) prev = snap.data() } catch {} }
  const next = serisiIsle(prev, today)
  saveStreak(next)
  localStorage.setItem(SK + '_last', today)
  if (uid && db && next.changed) {
    setDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.AKTIVITE, 'gunluk'), { current: next.current, longest: next.longest, lastDate: next.lastDate, updatedAt: serverTimestamp() }, { merge: true }).catch(() => {})
  }
  return next.current
}

// === Guest Stats (girişsiz kullanıcılar için) ===

export function guestStats() {
  return { konuDone: 0, denemeSayisi: 0, soruCozulen: 0, yanlisSayisi: 0, streakLongest: 0, sureDk: 0, sureHafta: {}, dersSure: {}, kullanimDk: 0, dogruCevap: 0, planGorev: 0 }
}

// === Sure Ekle (guest/localStorage fallback) ===

export function sureEkle(uid, dk, ders) {
  if (!dk) return
  const today = bugunStr()
  const patch = { sureDk: increment(dk), sureHafta: { [today]: increment(dk) }, updatedAt: serverTimestamp() }
  if (ders) patch.dersSure = { [ders]: increment(dk) }
  if (uid && db) {
    setDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.ISTATISTIK, 'genel'), patch, { merge: true }).catch(() => {})
  } else {
    // localStorage fallback
    try {
      const s = JSON.parse(localStorage.getItem('unisense_sure') || '{}')
      s.sureDk = (s.sureDk || 0) + dk
      s.sureHafta = s.sureHafta || {}
      s.sureHafta[today] = (s.sureHafta[today] || 0) + dk
      if (ders) { s.dersSure = s.dersSure || {}; s.dersSure[ders] = (s.dersSure[ders] || 0) + dk }
      localStorage.setItem('unisense_sure', JSON.stringify(s))
    } catch { /* noop */ }
  }
}