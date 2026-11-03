/**
 * Firebase Initialization — tek kaynak, tek yerde.
 * .env.local içindeki VITE_FIREBASE_* değişkenleri ile init.
 */
import { initializeApp, type FirebaseApp } from 'firebase/app'
import { initializeAppCheck, ReCaptchaV3Provider } from 'firebase/app-check'
import { getAuth, GoogleAuthProvider, type Auth } from 'firebase/auth'
import { getFirestore, type Firestore } from 'firebase/firestore'
import { getStorage, type FirebaseStorage } from 'firebase/storage'

const projectId = import.meta.env.VITE_FIREBASE_PROJECT_ID

const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  // authDomain Firebase'in kendi alanı OLMALI: site Vercel'de, unisense.com.tr
  // /__/auth/handler'ı sunmuyor (SPA index.html döner) ve Google OAuth
  // istemcisinde o redirect_uri kayıtlı değil → Google girişi
  // redirect_uri_mismatch / boş sayfa. Env'e bağlanmadı: Vercel'deki eski
  // VITE_FIREBASE_AUTH_DOMAIN değeri bu hatayı geri getirmesin.
  authDomain: `${projectId}.firebaseapp.com`,
  projectId,
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID,
  appId: import.meta.env.VITE_FIREBASE_APP_ID,
  measurementId: import.meta.env.VITE_FIREBASE_MEASUREMENT_ID,
}

// Firebase init — .env.local yoksa hata verme, sadece warning
let app: FirebaseApp | null = null
let auth: Auth | null = null
let db: Firestore | null = null
let storage: FirebaseStorage | null = null
let googleProvider: GoogleAuthProvider | null = null
let appCheck: any = null

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
      console.warn('App Check başlatılamadı:', (e as Error)?.message || e)
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