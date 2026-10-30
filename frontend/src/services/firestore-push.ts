/**
 * Firestore Push/Messaging Service — FCM bildirimleri, avatar upload.
 */
import { FIRESTORE_COLLECTIONS } from './constants'
import { app, db, addDoc, collection, query as fbQuery, orderBy, onSnapshot, getDocs, setDoc, updateDoc, deleteDoc, writeBatch, doc, serverTimestamp, getDoc } from './firestore-core'
import { getMessaging, getToken, deleteToken, isSupported as isMessagingSupported } from 'firebase/messaging'
import { getStorage, ref as storageRef, uploadBytes, getDownloadURL } from 'firebase/storage'

const VAPID_KEY = import.meta.env.VITE_FIREBASE_VAPID_KEY

export async function pushAvailable(): Promise<boolean> {
  if (!app || !VAPID_KEY) return false
  try { return await isMessagingSupported() } catch { return false }
}

export async function enablePush(uid: string): Promise<{ ok: boolean; reason?: string }> {
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

export async function disablePush(uid: string): Promise<void> {
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

export async function uploadAvatar(uid: string, file: File): Promise<string> {
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

export async function logQuery(uid: string, queryText: string, response: any): Promise<void> {
  if (!db) return
  try {
    await addDoc(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.QUERIES), {
      query: queryText, response_preview: (response?.text || '').slice(0, 500),
      doc_count: response?.docs?.length || 0, latency_ms: response?.total_latency_ms || null, ts: serverTimestamp(),
    })
  } catch (e) { console.warn('Query log fail', e) }
}

export function watchSessions(uid: string, callback: (data: any[]) => void): () => void {
  if (!db) return () => {}
  const q = fbQuery(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS), orderBy('updatedAt', 'desc'))
  return onSnapshot(q, (snap: any) => callback(snap.docs.map((d: any) => ({ id: d.id, ...d.data() }))))
}

export function watchSessionMessages(uid: string, sessionId: string, callback: (data: any[]) => void): () => void {
  if (!db || !sessionId) return () => {}
  const q = fbQuery(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS, sessionId, 'messages'), orderBy('createdAt', 'asc'))
  return onSnapshot(q, (snap: any) => callback(snap.docs.map((d: any) => ({ id: d.id, ...d.data() }))))
}

export async function createSession(uid: string, firstQuery: string = ''): Promise<string> {
  if (!db) throw new Error('Firebase yok')
  const sessionsRef = collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS)
  const allSnap = await getDocs(fbQuery(sessionsRef, orderBy('updatedAt', 'desc')))
  if (allSnap.size >= 5) {
    const oldestDocs = allSnap.docs.slice(4)
    for (const d of oldestDocs) await deleteSession(uid, d.id)
  }
  const ref = doc(sessionsRef)
  const title = firstQuery.slice(0, 60).trim() || 'Yeni Sohbet'
  await setDoc(ref, { title, messageCount: 0, createdAt: serverTimestamp(), updatedAt: serverTimestamp() })
  return ref.id
}

export async function updateSessionTitle(uid: string, sessionId: string, title: string): Promise<void> {
  if (!db) return
  await updateDoc(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS, sessionId), { title: title.slice(0, 60), updatedAt: serverTimestamp() })
}

export async function addSessionMessage(uid: string, sessionId: string, message: any): Promise<string | null> {
  if (!db || !sessionId) return null
  const messagesRef = collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS, sessionId, 'messages')
  const docRef = await addDoc(messagesRef, { ...message, createdAt: serverTimestamp() })
  const sessionRef = doc(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS, sessionId)
  const sessionSnap = await getDoc(sessionRef)
  const currentCount = sessionSnap.exists() ? (sessionSnap.data().messageCount || 0) : 0
  await updateDoc(sessionRef, { messageCount: currentCount + 1, updatedAt: serverTimestamp() })
  return docRef.id
}

export async function deleteSession(uid: string, sessionId: string): Promise<void> {
  if (!db || !sessionId) return
  const messagesRef = collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS, sessionId, 'messages')
  const messagesSnap = await getDocs(messagesRef)
  const batch = writeBatch(db)
  messagesSnap.docs.forEach((m: any) => batch.delete(m.ref))
  batch.delete(doc(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS, sessionId))
  await batch.commit()
}

export async function getSessionCount(uid: string): Promise<number> {
  if (!db) return 0
  const snap = await getDocs(collection(db, 'users', uid, FIRESTORE_COLLECTIONS.SESSIONS))
  return snap.size
}

export async function setEmailReminders(uid: string, on: boolean): Promise<void> {
  if (!db || !uid) throw new Error('giriş gerekli')
  await setDoc(doc(db, 'users', uid), { emailReminders: !!on }, { merge: true })
}