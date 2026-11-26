/**
 * Firebase Auth Service — kimlik doğrulama işlemleri.
 * firebase.js'den çıkarılan auth bölümleri.
 */
import {
  getAuth,
  GoogleAuthProvider,
  signInWithPopup,
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  updateProfile,
  updatePassword,
  EmailAuthProvider,
  reauthenticateWithCredential,
  reauthenticateWithPopup,
  deleteUser,
  type Auth,
  type User,
  type UserCredential,
} from 'firebase/auth'
import type { DocumentReference } from 'firebase/firestore'
import { app } from './firebase-init'
import {
  db,
  doc,
  setDoc,
  getDocs,
  collection,
  deleteDoc,
  writeBatch,
  serverTimestamp,
} from './firestore-core'
import { ensureUserDoc } from './firestore-user'

let auth: Auth | null = null
let googleProvider: GoogleAuthProvider | null = null

if (app) {
  auth = getAuth(app)
  googleProvider = new GoogleAuthProvider()
  googleProvider.setCustomParameters({ prompt: 'select_account' })
}

export { auth, googleProvider }

export async function loginWithGoogle(examTrack?: string): Promise<User> {
  if (!auth || !googleProvider) throw new Error('Firebase Auth yok')
  const result: UserCredential = await signInWithPopup(auth, googleProvider)
  await ensureUserDoc(result.user, examTrack)
  return result.user
}

export async function loginWithEmail(email: string, password: string): Promise<User> {
  if (!auth) throw new Error('Firebase Auth yok')
  const result: UserCredential = await signInWithEmailAndPassword(auth, email, password)
  await ensureUserDoc(result.user)
  return result.user
}

export async function registerWithEmail(
  email: string,
  password: string,
  displayName?: string,
  examTrack?: string,
): Promise<User> {
  if (!auth) throw new Error('Firebase Auth yok')
  const result: UserCredential = await createUserWithEmailAndPassword(auth, email, password)
  if (displayName) {
    await updateProfile(result.user, { displayName })
  }
  await ensureUserDoc(result.user, examTrack)
  return result.user
}

export async function logout(): Promise<void> {
  if (!auth) return
  await signOut(auth)
}

export function watchAuth(callback: (user: User | null) => void): () => void {
  if (!auth) return () => {}
  return onAuthStateChanged(auth, callback)
}

export async function updateUserBasicInfo(
  user: User,
  { displayName, photoURL }: { displayName?: string; photoURL?: string },
): Promise<void> {
  if (!auth) throw new Error('Firebase Auth yok')
  const updates: { displayName?: string; photoURL?: string } = {}
  if (displayName !== undefined) updates.displayName = displayName.slice(0, 100)
  if (photoURL !== undefined) updates.photoURL = photoURL.slice(0, 1000)
  if (Object.keys(updates).length === 0) return
  await updateProfile(user, updates)
  if (db) {
    await setDoc(
      doc(db, 'users', user.uid),
      { ...updates, updatedAt: serverTimestamp() },
      { merge: true },
    )
  }
}

const USER_SUBCOLLECTIONS = [
  'tercih',
  'dgs_tercih',
  'kpss_tercih',
  'tus_tercih',
  'dus_tercih',
  'lgs_tercih',
  'konu_ilerleme',
  'aktivite',
  'pushTokens',
  'yanlislar',
  'notlar',
  'kartlar',
  'istatistik',
  'denemeler',
  'soru_kayit',
  'plan_config',
  'plan_gorev',
  'queries',
  'sessions',
] as const

async function deleteRefsInBatches(refs: DocumentReference[]): Promise<void> {
  if (!db || refs.length === 0) return
  const BATCH_SIZE = 400
  for (let i = 0; i < refs.length; i += BATCH_SIZE) {
    const batch = writeBatch(db)
    for (const ref of refs.slice(i, i + BATCH_SIZE)) {
      batch.delete(ref)
    }
    await batch.commit()
  }
}

export async function deleteAccountAndData(
  user: User,
  currentPassword?: string,
): Promise<void> {
  if (!auth) throw new Error('Firebase Auth yok')

  const provider = getAuthProvider(user)
  if (provider === 'google') {
    if (!googleProvider) throw new Error('Google sağlayıcısı hazır değil')
    await reauthenticateWithPopup(user, googleProvider)
  } else {
    if (!currentPassword) {
      throw new Error('Hesabı silmek için mevcut şifreni girmelisin')
    }
    if (!user.email) {
      throw new Error('E-posta bilgisi bulunamadı')
    }
    const cred = EmailAuthProvider.credential(user.email, currentPassword)
    await reauthenticateWithCredential(user, cred)
  }

  if (db) {
    for (const sub of USER_SUBCOLLECTIONS) {
      if (sub === 'sessions') {
        const sessionsSnap = await getDocs(collection(db, 'users', user.uid, 'sessions'))
        for (const sessionDoc of sessionsSnap.docs) {
          const msgsSnap = await getDocs(
            collection(db, 'users', user.uid, 'sessions', sessionDoc.id, 'messages'),
          )
          await deleteRefsInBatches(msgsSnap.docs.map((d) => d.ref))
        }
        await deleteRefsInBatches(sessionsSnap.docs.map((d) => d.ref))
      } else {
        const snap = await getDocs(collection(db, 'users', user.uid, sub))
        await deleteRefsInBatches(snap.docs.map((d) => d.ref))
      }
    }

    await deleteDoc(doc(db, 'siralama', user.uid))
    await deleteDoc(doc(db, 'users', user.uid))
  }

  await deleteUser(user)

  if (typeof window !== 'undefined' && window.localStorage) {
    const keysToRemove: string[] = []
    for (let i = 0; i < window.localStorage.length; i++) {
      const k = window.localStorage.key(i)
      if (k && k.startsWith('unisense_')) {
        keysToRemove.push(k)
      }
    }
    for (const k of keysToRemove) {
      window.localStorage.removeItem(k)
    }
  }
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  if (!auth || !auth.currentUser) throw new Error('Giriş yapmamışsın')
  const user = auth.currentUser
  if (!user.email) {
    throw new Error('Şifre değiştirme sadece e-posta hesapları için')
  }
  const cred = EmailAuthProvider.credential(user.email, currentPassword)
  await reauthenticateWithCredential(user, cred)
  await updatePassword(user, newPassword)
}

export function getAuthProvider(user: User | null): string | null {
  if (!user) return null
  const providers = user.providerData?.map((p) => p.providerId) || []
  if (providers.includes('google.com')) return 'google'
  if (providers.includes('password')) return 'email'
  return providers[0] || 'unknown'
}