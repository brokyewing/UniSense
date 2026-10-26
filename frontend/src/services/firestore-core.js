/**
 * Firestore User Service — kullanıcı profili ve alt koleksiyonları (temel CRUD).
 */
import {
  getFirestore,
  doc as _doc,
  setDoc as _setDoc,
  getDoc as _getDoc,
  getDocs as _getDocs,
  updateDoc as _updateDoc,
  collection as _collection,
  addDoc as _addDoc,
  query as _query,
  where as _where,
  orderBy as _orderBy,
  limit as _limit,
  onSnapshot as _onSnapshot,
  deleteDoc as _deleteDoc,
  serverTimestamp as _serverTimestamp,
  writeBatch as _writeBatch,
  increment as _increment,
  deleteField as _deleteField,
  getCountFromServer as _getCountFromServer,
} from 'firebase/firestore'
import { app, db } from './firebase-init'
import { FIRESTORE_COLLECTIONS, MAX_SESSIONS_PER_USER } from './constants'

// Re-export individual functions to avoid Vite dev server issues
export const doc = _doc
export const setDoc = _setDoc
export const getDoc = _getDoc
export const getDocs = _getDocs
export const updateDoc = _updateDoc
export const collection = _collection
export const addDoc = _addDoc
export const query = _query
export const where = _where
export const orderBy = _orderBy
export const limit = _limit
export const onSnapshot = _onSnapshot
export const deleteDoc = _deleteDoc
export const serverTimestamp = _serverTimestamp
export const writeBatch = _writeBatch
export const increment = _increment
export const deleteField = _deleteField
export const getCountFromServer = _getCountFromServer
export { db, app }

// === User Profile ===

export async function ensureUserDoc(user, examTrack) {
  if (!db) return
  const ref = doc(db, 'users', user.uid)
  const snap = await getDoc(ref)
  if (!snap.exists()) {
    await setDoc(ref, {
      uid: user.uid, ...(user.email ? { email: user.email } : {}),
      displayName: user.displayName || '', photoURL: user.photoURL || '',
      createdAt: serverTimestamp(),
      profile: { examTrack: examTrack || 'YKS', scoreType: null, score: null, rank: null, preferredCities: [] },
    })
  } else if (examTrack) {
    await setDoc(ref, { profile: { examTrack } }, { merge: true })
  }
}

export async function getUserProfile(uid) {
  if (!db) return null
  const snap = await getDoc(doc(db, 'users', uid))
  return snap.exists() ? snap.data() : null
}

export async function updateUserProfile(uid, profile) {
  if (!db) throw new Error('Firestore yok')
  await setDoc(doc(db, 'users', uid), { profile, updatedAt: serverTimestamp() }, { merge: true })
}

// === Generic Subcollection Helpers ===

export function watchSubcollection(uid, subcollection, callback, options = {}) {
  if (!db || !uid) { callback(options.where ? [] : {}); return () => {} }
  const constraints = []
  if (options.where) constraints.push(where(...options.where))
  if (options.orderBy) constraints.push(orderBy(options.orderBy, options.orderDir || 'asc'))
  if (options.limit) constraints.push(limit(options.limit))
  const q = query(collection(db, 'users', uid, subcollection), ...constraints)
  return onSnapshot(q, (snap) => {
    const items = snap.docs.map(d => ({ id: d.id, ...d.data() }))
    callback(options.where ? items : items.reduce((acc, item) => { acc[item.id] = item; return acc }, {}))
  }, () => callback(null))
}

export async function getSubcollectionDoc(uid, subcollection, docId) {
  if (!db || !uid) return null
  try { const snap = await getDoc(doc(db, 'users', uid, subcollection, docId)); return snap.exists() ? { id: snap.id, ...snap.data() } : null } catch { return null }
}

export async function getSubcollectionAll(uid, subcollection, constraints = []) {
  if (!db || !uid) return []
  try { const q = query(collection(db, 'users', uid, subcollection), ...constraints); const snap = await getDocs(q); return snap.docs.map(d => ({ id: d.id, ...d.data() })) } catch { return [] }
}

export async function addSubcollectionDoc(uid, subcollection, data) {
  if (!db || !uid) return null
  const ref = await addDoc(collection(db, 'users', uid, subcollection), { ...data, createdAt: serverTimestamp() })
  return ref.id
}

export async function setSubcollectionDoc(uid, subcollection, docId, data, merge = false) {
  if (!db || !uid) return
  await setDoc(doc(db, 'users', uid, subcollection, docId), { ...data, updatedAt: serverTimestamp() }, { merge })
}

export async function updateSubcollectionDoc(uid, subcollection, docId, patch) {
  if (!db || !uid) return
  await updateDoc(doc(db, 'users', uid, subcollection, docId), { ...patch, updatedAt: serverTimestamp() })
}

export async function deleteSubcollectionDoc(uid, subcollection, docId) {
  if (!db || !uid) return
  await deleteDoc(doc(db, 'users', uid, subcollection, docId))
}

export async function batchWrite(uid, operations) {
  if (!db || !uid || !operations.length) return
  const batch = writeBatch(db)
  for (const op of operations) {
    const { type, subcollection, docId, data } = op
    const ref = doc(db, 'users', uid, subcollection, docId)
    if (type === 'set') batch.set(ref, { ...data, updatedAt: serverTimestamp() }, { merge: true })
    else if (type === 'update') batch.update(ref, { ...data, updatedAt: serverTimestamp() })
    else if (type === 'delete') batch.delete(ref)
  }
  await batch.commit()
}