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
  // Google ekranında "unisense.com.tr'ye devam edin" görünsün diye özel alan.
  // Üç parçaya bağlı — biri eksikse Google girişi boş sayfa /
  // redirect_uri_mismatch verir:
  //  1. vercel.json: /__/auth/* → unisense-13634.firebaseapp.com proxy'si
  //     (SPA catch-all'dan ÖNCE)
  //  2. Google OAuth istemcisi: https://www.unisense.com.tr/__/auth/handler
  //  3. Firebase authorized domains: www.unisense.com.tr
  // www (çıplak alan değil): unisense.com.tr Vercel'de www'ya 308 yapar.
  // Env'e bağlanmadı: Vercel'deki eski VITE_FIREBASE_AUTH_DOMAIN değeri
  // (unisense.com.tr) bu ayarı ezmesin.
  authDomain: 'www.unisense.com.tr',
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