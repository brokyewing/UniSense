/**
 * Firestore User Service — kullanıcı profili işlemleri.
 */
import { db, doc, getDoc, setDoc, serverTimestamp } from './firestore-core'

export async function ensureUserDoc(user, examTrack) {
  if (!db || !user) return
  const ref = doc(db, 'users', user.uid)
  const snap = await getDoc(ref)
  if (!snap.exists()) {
    await setDoc(ref, {
      uid: user.uid,
      ...(user.email ? { email: user.email } : {}),
      displayName: user.displayName || '',
      photoURL: user.photoURL || '',
      createdAt: serverTimestamp(),
      profile: {
        examTrack: examTrack || 'YKS',
        scoreType: null,
        score: null,
        rank: null,
        preferredCities: [],
      },
    })
  } else if (examTrack) {
    await setDoc(ref, { profile: { examTrack } }, { merge: true })
  }
}