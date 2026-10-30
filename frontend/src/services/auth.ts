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
  type Auth,
  type User,
  type UserCredential,
} from 'firebase/auth'
import { app } from './firebase-init'
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
  const updates: Record<string, string> = {}
  if (displayName !== undefined) updates.displayName = displayName
  if (photoURL !== undefined) updates.photoURL = photoURL
  if (Object.keys(updates).length > 0) {
    await updateProfile(user, updates)
  }
  // Firestore güncellemesi ensureUserDoc/zaten ayrı yapılıyor
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