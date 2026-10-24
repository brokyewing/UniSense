/**
 * Firestore Push/Messaging Service — FCM bildirimleri, avatar upload.
 */
import { FIRESTORE_COLLECTIONS } from './constants'
import { app, db, addDoc, collection, query as fbQuery, orderBy, onSnapshot, getDocs, setDoc, updateDoc, deleteDoc, writeBatch, doc, serverTimestamp } from './firestore-core'
import { getMessaging, getToken, deleteToken, isSupported as isMessagingSupported } from 'firebase/messaging'
import { getStorage, ref as storageRef, uploadBytes, getDownloadURL } from 'firebase/storage'

const VAPID_KEY = import.meta.env.VITE_FIREBASE_VAPID_KEY

export async function pushAvailable() {
  if (!app || !VAPID_KEY) return false
  try { return await isMessagingSupported() } catch { return false }
}

export async function enablePush(uid) {
  if (!app || !db || !uid) return { ok: false, reason: 'no-auth' }
  if (!VAPID_KEY) return { ok: false, reason: 'no-vapid' }
  if (!(await isMessagingSupported().catch(() => false))) return { ok: false, reason: 'unsupported' }
  const perm = await Notification.requestPermission()
  if (perm !== 'granted') return { ok: false, reason: 'denied' }

  const firebaseConfig = {
    apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
    projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
    appId: import.meta.env.VITE_FIREBASE_APP_ID,
  }

  const swReg = await navigator.serviceWorker.register(
    `/firebase-messaging-sw.js?${new URLSearchParams({
      apiKey: firebaseConfig.apiKey || '', projectId: firebaseConfig.projectId || '',
      messagingSenderId: firebaseConfig.messagingSenderId || '', appId: firebaseConfig.appId || '',
    }).toString()}`, { scope: '/firebase-cloud-messaging-push-scope' }
  )
  const messaging = getMessaging(app)
  const token = await getToken(messaging, { vapidKey: VAPID_KEY, serviceWorkerRegistration: swReg })
  if (!token) return { ok: false, reason: 'no-token' }
  await setDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.PUSH_TOKENS, token), {
    token, ua: (navigator.userAgent || '').slice(0, 300), updatedAt: serverTimestamp()
  }, { merge: true })
  return { ok: true }
}

export async function setEmailReminders(uid, on) {
  if (!db || !uid) throw new Error('giriş gerekli')
  await setDoc(doc(db, 'users', uid), { emailReminders: !!on }, { merge: true })
}

export async function disablePush(uid) {
  if (!app || !db || !uid) return
  try {
    if (await isMessagingSupported().catch(() => false)) {
      const messaging = getMessaging(app)
      const token = await getToken(messaging, { vapidKey: VAPID_KEY }).catch(() => null)
      if (token) {
        await deleteDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.PUSH_TOKENS, token)).catch(() => {})
        await deleteToken(messaging).catch(() => {})
      }
    }
  } catch {}
}

export async function uploadAvatar(uid, file) {
  const storage = app ? getStorage(app) : null
  if (!storage) throw new Error('Firebase Storage yok')
  if (file.size > 5 * 1024 * 1024) throw new Error('Dosya çok büyük (max 5 MB)')
  const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/webp']
  if (!ALLOWED_TYPES.includes(file.type)) throw new Error('Sadece PNG, JPEG veya WebP kabul edilir')
  const ext = (file.name.split('.').pop() || 'png').toLowerCase()
  const ref = storageRef(storage, `avatars/${uid}/avatar-${Date.now()}.${ext}`)
  await uploadBytes(ref, file, { contentType: file.type })
  return await getDownloadURL(ref)
}

// === Query History ===

export async function logQuery(uid, queryText, response) {
  if (!db) return
  try {
    await addDoc(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.QUERIES), {
      query: queryText, response_preview: (response?.text || '').slice(0, 500),
      doc_count: response?.docs?.length || 0, latency_ms: response?.total_latency_ms || null, ts: serverTimestamp(),
    })
  } catch (e) { console.warn('Query log fail', e) }
}

// === Chat Sessions ===

export function watchSessions(uid, callback) {
  if (!db) return () => {}
  const q = fbQuery(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS), orderBy('updatedAt', 'desc'))
  return onSnapshot(q, (snap) => callback(snap.docs.map(d => ({ id: d.id, ...d.data() }))))
}

export function watchSessionMessages(uid, sessionId, callback) {
  if (!db || !sessionId) return () => {}
  const q = fbQuery(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS, sessionId, 'messages'), orderBy('createdAt', 'asc'))
  return onSnapshot(q, (snap) => callback(snap.docs.map(d => ({ id: d.id, ...d.data() }))))
}

export async function createSession(uid, firstQuery = '') {
  if (!db) throw new Error('Firestore yok')
  const sessionsRef = collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS)
  const allSnap = await getDocs(fbQuery(sessionsRef, orderBy('updatedAt', 'desc')))
  if (allSnap.size >= MAX_SESSIONS_PER_USER) {
    const oldestDocs = allSnap.docs.slice(MAX_SESSIONS_PER_USER - 1)
    for (const d of oldestDocs) await deleteSession(uid, d.id)
  }
  const ref = doc(sessionsRef)
  const title = firstQuery.slice(0, 60).trim() || 'Yeni Sohbet'
  await setDoc(ref, { title, messageCount: 0, createdAt: serverTimestamp(), updatedAt: serverTimestamp() })
  return ref.id
}

export async function updateSessionTitle(uid, sessionId, title) {
  if (!db) return
  await updateDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS, sessionId), { title: title.slice(0, 60), updatedAt: serverTimestamp() })
}

export async function addSessionMessage(uid, sessionId, message) {
  if (!db || !sessionId) return null
  const messagesRef = collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS, sessionId, 'messages')
  const docRef = await addDoc(messagesRef, { ...message, createdAt: serverTimestamp() })
  const sessionRef = doc(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS, sessionId)
  const sessionSnap = await getDoc(sessionRef)
  const currentCount = sessionSnap.exists() ? (sessionSnap.data().messageCount || 0) : 0
  await updateDoc(sessionRef, { messageCount: currentCount + 1, updatedAt: serverTimestamp() })
  return docRef.id
}

export async function deleteSession(uid, sessionId) {
  if (!db || !sessionId) return
  const messagesRef = collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS, sessionId, 'messages')
  const messagesSnap = await getDocs(messagesRef)
  const batch = writeBatch(db)
  messagesSnap.docs.forEach(m => batch.delete(m.ref))
  batch.delete(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS, sessionId))
  await batch.commit()
}

export async function getSessionCount(uid) {
  if (!db) return 0
  const snap = await getDocs(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS))
  return snap.size
}