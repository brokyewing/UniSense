/**
 * Firestore Study Tracking Service — konu, deneme, soru, yanlış, notlar, kartlar.
 */
import {
  db,
  watchSubcollection, getSubcollectionDoc, addSubcollectionDoc, updateSubcollectionDoc, deleteSubcollectionDoc,
  batchWrite, setSubcollectionDoc, getSubcollectionAll,
  increment, serverTimestamp, writeBatch, deleteField, getCountFromServer,
  getDoc, getDocs, collection, doc, query, orderBy, where, limit, onSnapshot, updateDoc, deleteDoc, addDoc, setDoc,
} from './firestore-core'
import { FIRESTORE_COLLECTIONS } from './constants'
import { serisiIsle, bugunStr, guncelSeri } from '../lib/streak'

// === Konu İlerleme (checked haritası — tek belge per sınav) ===

export function watchKonuIlerleme(uid, sinav, callback) {
  return watchSubcollection(uid, FIRESTORE_COLLECTIONS.KONU_ILERLEME, (data) => {
    const item = data[sinav] || {}
    callback(item.checked || {})
  }, { where: ['__name__', '==', sinav] })
}

export async function getKonuIlerleme(uid, sinav) {
  const item = await getSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.KONU_ILERLEME, sinav)
  return item?.checked || {}
}

export async function setKonuIlerleme(uid, sinav, checked) {
  await setSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.KONU_ILERLEME, sinav, { checked })
}

// === Deneme Günlüğü ===

export function watchDenemeler(uid, sinav, callback) {
  return watchSubcollection(uid, FIRESTORE_COLLECTIONS.DENEMELER, callback, {
    where: ['sinav', '==', sinav], orderBy: 'tarih', orderDir: 'asc',
  })
}

export const addDeneme = (uid, data) => addSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.DENEMELER, data)
export const removeDeneme = (uid, id) => deleteSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.DENEMELER, id)

// === Çözülen Soru Kaydı ===

export function watchSoruKayit(uid, sinav, callback) {
  return watchSubcollection(uid, FIRESTORE_COLLECTIONS.SORU_KAYIT, callback, {
    where: ['sinav', '==', sinav], orderBy: 'tarih', orderDir: 'desc',
  })
}

export const addSoruKayit = (uid, data) => addSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.SORU_KAYIT, data)
export const removeSoruKayit = (uid, id) => deleteSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.SORU_KAYIT, id)

// === Yanlış Defteri ===

export function watchYanlislar(uid, callback) {
  return watchSubcollection(uid, FIRESTORE_COLLECTIONS.YANLISLAR, callback, {
    orderBy: 'createdAt', orderDir: 'desc',
  })
}

export const addYanlis = (uid, data) => addSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.YANLISLAR, data)
export const updateYanlis = (uid, id, patch) => updateSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.YANLISLAR, id, patch)
export const removeYanlis = (uid, id) => deleteSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.YANLISLAR, id)

// === Notlar ===

export function watchNotlar(uid, callback) {
  return watchSubcollection(uid, FIRESTORE_COLLECTIONS.NOTLAR, callback, {
    orderBy: 'createdAt', orderDir: 'desc',
  })
}

export const addNot = (uid, data) => addSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.NOTLAR, data)
export const updateNot = (uid, id, patch) => updateSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.NOTLAR, id, patch)
export const removeNot = (uid, id) => deleteSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.NOTLAR, id)

// === Kartlar (Flashcard) ===

export function watchKartlar(uid, callback) {
  return watchSubcollection(uid, FIRESTORE_COLLECTIONS.KARTLAR, callback, {
    orderBy: 'createdAt', orderDir: 'desc',
  })
}

export const addKart = (uid, data) => addSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.KARTLAR, data)
export const updateKart = (uid, id, patch) => updateSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.KARTLAR, id, patch)
export const removeKart = (uid, id) => deleteSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.KARTLAR, id)

// === İstatistik / Çalışma Süresi ===

export async function sureEkle(uid, dk, ders) {
  if (!db || !uid || !dk) return
  const today = new Date().toISOString().slice(0, 10)
  const patch = { sureDk: increment(dk), sureHafta: { [today]: increment(dk) }, updatedAt: serverTimestamp() }
  if (ders) patch.dersSure = { [ders]: increment(dk) }
  await setSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.ISTATISTIK, 'genel', patch, true).catch(() => {})
}

export async function kullanimEkle(uid, dk) {
  if (!db || !uid || !dk) return
  await setSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.ISTATISTIK, 'genel', { kullanimDk: increment(dk), updatedAt: serverTimestamp() }, true)
}