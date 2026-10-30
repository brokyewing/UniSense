/**
 * Firestore Study Tracking Service — konu, deneme, soru, yanlış, notlar, kartlar.
 */
import {
  db,
  watchSubcollection, getSubcollectionDoc, addSubcollectionDoc, updateSubcollectionDoc, deleteSubcollectionDoc,
  setSubcollectionDoc, increment, serverTimestamp,
} from './firestore-core'
import { FIRESTORE_COLLECTIONS } from './constants'

// === Konu İlerleme (checked haritası — tek belge per sınav) ===

export function watchKonuIlerleme(uid: string, sinav: string, callback: (data: any) => void): () => void {
  return watchSubcollection(uid, FIRESTORE_COLLECTIONS.KONU_ILERLEME, (data: any) => {
    const item = (data && data[sinav]) || {}
    callback(item.checked || {})
  }, { where: ['__name__', '==', sinav] })
}

export async function getKonuIlerleme(uid: string, sinav: string): Promise<any> {
  const item = await getSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.KONU_ILERLEME, sinav)
  return item?.checked || {}
}

export async function setKonuIlerleme(uid: string, sinav: string, checked: any): Promise<void> {
  await setSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.KONU_ILERLEME, sinav, { checked })
}

// === Deneme Günlüğü ===

export function watchDenemeler(uid: string, sinav: string, callback: (data: any) => void): () => void {
  return watchSubcollection(uid, FIRESTORE_COLLECTIONS.DENEMELER, callback, {
    where: ['sinav', '==', sinav], orderBy: 'tarih', orderDir: 'asc',
  })
}

export const addDeneme = (uid: string, data: any) => addSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.DENEMELER, data)
export const removeDeneme = (uid: string, id: string) => deleteSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.DENEMELER, id)

// === Çözülen Soru Kaydı ===

export function watchSoruKayit(uid: string, sinav: string, callback: (data: any) => void): () => void {
  return watchSubcollection(uid, FIRESTORE_COLLECTIONS.SORU_KAYIT, callback, {
    where: ['sinav', '==', sinav], orderBy: 'tarih', orderDir: 'desc',
  })
}

export const addSoruKayit = (uid: string, data: any) => addSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.SORU_KAYIT, data)
export const removeSoruKayit = (uid: string, id: string) => deleteSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.SORU_KAYIT, id)

// === Yanlış Defteri ===

export function watchYanlislar(uid: string, callback: (data: any) => void): () => void {
  return watchSubcollection(uid, FIRESTORE_COLLECTIONS.YANLISLAR, callback, {
    orderBy: 'createdAt', orderDir: 'desc',
  })
}

export const addYanlis = (uid: string, data: any) => addSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.YANLISLAR, data)
export const updateYanlis = (uid: string, id: string, patch: any) => updateSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.YANLISLAR, id, patch)
export const removeYanlis = (uid: string, id: string) => deleteSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.YANLISLAR, id)

// === Notlar ===

export function watchNotlar(uid: string, callback: (data: any) => void): () => void {
  return watchSubcollection(uid, FIRESTORE_COLLECTIONS.NOTLAR, callback, {
    orderBy: 'createdAt', orderDir: 'desc',
  })
}

export const addNot = (uid: string, data: any) => addSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.NOTLAR, data)
export const updateNot = (uid: string, id: string, patch: any) => updateSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.NOTLAR, id, patch)
export const removeNot = (uid: string, id: string) => deleteSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.NOTLAR, id)

// === Kartlar (Flashcard) ===

export function watchKartlar(uid: string, callback: (data: any) => void): () => void {
  return watchSubcollection(uid, FIRESTORE_COLLECTIONS.KARTLAR, callback, {
    orderBy: 'createdAt', orderDir: 'desc',
  })
}

export const addKart = (uid: string, data: any) => addSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.KARTLAR, data)
export const updateKart = (uid: string, id: string, patch: any) => updateSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.KARTLAR, id, patch)
export const removeKart = (uid: string, id: string) => deleteSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.KARTLAR, id)

// === İstatistik / Çalışma Süresi ===

async function sureEkle(uid: string, dk: number, ders: string): Promise<void> {
  if (!db || !uid || !dk) return
  const today = new Date().toISOString().slice(0, 10)
  const patch: any = { sureDk: increment(dk), sureHafta: { [today]: increment(dk) }, updatedAt: serverTimestamp() }
  if (ders) patch.dersSure = { [ders]: increment(dk) }
  await setSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.ISTATISTIK, 'genel', patch, true).catch(() => {})
}

export async function kullanimEkle(uid: string, dk: number): Promise<void> {
  if (!db || !uid || !dk) return
  await setSubcollectionDoc(uid, FIRESTORE_COLLECTIONS.ISTATISTIK, 'genel', { kullanimDk: increment(dk), updatedAt: serverTimestamp() }, true)
}