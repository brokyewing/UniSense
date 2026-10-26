/**
 * Firebase Initialization — tek kaynak, tek yerde.
 * .env.local içindeki VITE_FIREBASE_* değişkenleri ile init.
 */
import { initializeApp } from 'firebase/app'
import { initializeAppCheck, ReCaptchaV3Provider } from 'firebase/app-check'
import { getAuth, GoogleAuthProvider } from 'firebase/auth'
import { getFirestore } from 'firebase/firestore'
import { getStorage } from 'firebase/storage'

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
}

// Firebase init — .env.local yoksa hata verme, sadece warning
let app = null
let auth = null
let db = null
let storage = null
let googleProvider = null
let appCheck = null

if (firebaseConfig.apiKey) {
  app = initializeApp(firebaseConfig)

  // App Check
  const recaptchaKey = import.meta.env.VITE_RECAPTCHA_SITE_KEY
  if (recaptchaKey) {
    try {
      appCheck = initializeAppCheck(app, {
        provider: new ReCaptchaV3Provider(recaptchaKey),
        isTokenAutoRefreshEnabled: true,
      })
    } catch (e) {
      console.warn('App Check başlatılamadı:', e?.message || e)
    }
  }

  auth = getAuth(app)
  db = getFirestore(app)
  storage = getStorage(app)
  googleProvider = new GoogleAuthProvider()
  googleProvider.setCustomParameters({ prompt: 'select_account' })
} else {
  console.warn('🔥 Firebase config bulunamadı (.env.local). Auth özellikleri devre dışı.')
}

export { app, auth, db, storage, googleProvider, appCheck }