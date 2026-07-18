/**
 * Firebase config + auth + firestore.
 * .env.local içindeki VITE_FIREBASE_* değişkenleri ile init.
 *
 * Firestore koleksiyonları:
 *   users/{uid}                  — kullanıcı profili (puan, sıralama, hedefler)
 *   users/{uid}/tercih/{order}   — tercih listesi (24 sıra max)
 *   users/{uid}/queries/{qid}    — sorgu geçmişi
 *   users/{uid}/sessions/{sid}   — sohbet oturumları (max 5)
 */
import { initializeApp } from 'firebase/app'
import { initializeAppCheck, ReCaptchaV3Provider } from 'firebase/app-check'
import { serisiIsle, bugunStr, guncelSeri } from './lib/streak'
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
} from 'firebase/auth'
import {
  getStorage,
  ref as storageRef,
  uploadBytes,
  getDownloadURL,
} from 'firebase/storage'
import {
  getMessaging,
  getToken,
  deleteToken,
  isSupported as isMessagingSupported,
} from 'firebase/messaging'
import {
  getFirestore,
  doc,
  setDoc,
  getDoc,
  getDocs,
  updateDoc,
  collection,
  addDoc,
  query,
  where,
  orderBy,
  limit,
  onSnapshot,
  deleteDoc,
  serverTimestamp,
  writeBatch,
} from 'firebase/firestore'

// Sabitler
export const MAX_SESSIONS_PER_USER = 5

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

  // App Check — istekleri GERÇEK uygulamadan geldiğine dair doğrular; konsolda
  // "Enforce" açılınca Firestore'a raw-SDK/REST ile (UI atlanarak) sınırsız
  // doküman yazma / doğrudan erişim engellenir. reCAPTCHA v3 site key'i env'de
  // varsa aktifleşir — yoksa (lokal dev) sessizce atlanır, uygulama çalışır.
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

// === HAZIR AVATAR'LAR (DiceBear API, ücretsiz) ===
// Internet erişimi olmasa bile çalışır (URL string)
export const PRESET_AVATARS = [
  { id: 'av1',  url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=UniSense01&backgroundColor=b6e3f4' },
  { id: 'av2',  url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=UniSense02&backgroundColor=ffd5dc' },
  { id: 'av3',  url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=UniSense03&backgroundColor=c0aede' },
  { id: 'av4',  url: 'https://api.dicebear.com/7.x/adventurer/svg?seed=UniSense04&backgroundColor=d1d4f9' },
  { id: 'av5',  url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=UniSense05&backgroundColor=b6e3f4' },
  { id: 'av6',  url: 'https://api.dicebear.com/7.x/avataaars/svg?seed=UniSense06&backgroundColor=ffdfbf' },
  { id: 'av7',  url: 'https://api.dicebear.com/7.x/lorelei/svg?seed=UniSense07&backgroundColor=ffd5dc' },
  { id: 'av8',  url: 'https://api.dicebear.com/7.x/lorelei/svg?seed=UniSense08&backgroundColor=b6e3f4' },
  { id: 'av9',  url: 'https://api.dicebear.com/7.x/notionists/svg?seed=UniSense09&backgroundColor=c0aede' },
  { id: 'av10', url: 'https://api.dicebear.com/7.x/notionists/svg?seed=UniSense10&backgroundColor=d1d4f9' },
  { id: 'av11', url: 'https://api.dicebear.com/7.x/bottts/svg?seed=UniSense11&backgroundColor=b6e3f4' },
  { id: 'av12', url: 'https://api.dicebear.com/7.x/bottts/svg?seed=UniSense12&backgroundColor=ffd5dc' },
]

// === AUTH HELPERS ===

export async function loginWithGoogle(examTrack) {
  if (!auth || !googleProvider) throw new Error('Firebase yok')
  const result = await signInWithPopup(auth, googleProvider)
  await ensureUserDoc(result.user, examTrack)
  return result.user
}

export async function loginWithEmail(email, password) {
  if (!auth) throw new Error('Firebase yok')
  const result = await signInWithEmailAndPassword(auth, email, password)
  await ensureUserDoc(result.user)
  return result.user
}

export async function registerWithEmail(email, password, displayName, examTrack) {
  if (!auth) throw new Error('Firebase yok')
  const result = await createUserWithEmailAndPassword(auth, email, password)
  if (displayName) {
    await updateProfile(result.user, { displayName })
  }
  await ensureUserDoc(result.user, examTrack)
  return result.user
}

export async function logout() {
  if (!auth) return
  await signOut(auth)
}

export function watchAuth(callback) {
  if (!auth) return () => {}
  return onAuthStateChanged(auth, callback)
}

async function ensureUserDoc(user, examTrack) {
  if (!db) return
  const ref = doc(db, 'users', user.uid)
  const snap = await getDoc(ref)
  if (!snap.exists()) {
    await setDoc(ref, {
      uid: user.uid,
      email: user.email,
      displayName: user.displayName || '',
      photoURL: user.photoURL || '',
      createdAt: serverTimestamp(),
      profile: {
        // Kayıtta seçilen sınav yolu — sorgu yönlendirmesini kolaylaştırır,
        // profilden değiştirilebilir
        examTrack: examTrack || 'YKS',
        scoreType: null,
        score: null,
        rank: null,
        preferredCities: [],
      },
    })
  } else if (examTrack) {
    // Kayıt ekranında yol seçip Google ile giren kullanıcının hesabı zaten
    // varsa seçim kaybolmasın — sadece examTrack'i güncelle
    await setDoc(ref, { profile: { examTrack } }, { merge: true })
  }
}

// === USER PROFILE ===

export async function getUserProfile(uid) {
  if (!db) return null
  const snap = await getDoc(doc(db, 'users', uid))
  return snap.exists() ? snap.data() : null
}

export async function updateUserProfile(uid, profile) {
  if (!db) throw new Error('Firebase yok')
  await setDoc(doc(db, 'users', uid), { profile, updatedAt: serverTimestamp() }, { merge: true })
}

// === Konu takip ilerlemesi (bulut senkronu — sınav başına 1 doküman) ===
/** Realtime izle: checked haritasını verir; erişilemezse (kural/App Check) null → çağıran localStorage'a düşer. */
export function watchKonuIlerleme(uid, sinav, callback) {
  if (!db || !uid) { callback(null); return () => {} }
  return onSnapshot(
    doc(db, 'users', uid, 'konu_ilerleme', sinav),
    (snap) => callback(snap.exists() ? (snap.data().checked || {}) : {}),
    () => callback(null),  // izin/erişim hatası → null (localStorage'a düş)
  )
}

/** Tüm checked haritasını yaz (küçük; her tik'te tam harita — deleteField karmaşası yok). */
export async function setKonuIlerleme(uid, sinav, checked) {
  if (!db || !uid) return
  await setDoc(
    doc(db, 'users', uid, 'konu_ilerleme', sinav),
    { checked, updatedAt: serverTimestamp() },
    { merge: true },
  )
}

// === Deneme günlüğü (bulut — her deneme 1 doküman) ===
/** Seçili sınavın denemelerini tarih sırasıyla izle. Erişilemezse null → çağıran localStorage. */
export function watchDenemeler(uid, sinav, callback) {
  if (!db || !uid) { callback([]); return () => {} }
  const q = query(collection(db, 'users', uid, 'denemeler'), where('sinav', '==', sinav))
  return onSnapshot(q, (snap) => {
    const items = snap.docs.map((d) => ({ id: d.id, ...d.data() }))
    items.sort((a, b) => (a.tarih || '').localeCompare(b.tarih || '')) // eski→yeni
    callback(items)
  }, () => callback(null))
}

export async function addDeneme(uid, deneme) {
  if (!db || !uid) return null
  const ref = await addDoc(collection(db, 'users', uid, 'denemeler'),
    { ...deneme, createdAt: serverTimestamp() })
  return ref.id
}

export async function removeDeneme(uid, id) {
  if (!db || !uid) return
  await deleteDoc(doc(db, 'users', uid, 'denemeler', id))
}

// === Yanlış Defteri (bulut — her yanlış 1 doküman; metin tabanlı) ===
/** Yanlışları en yeni→eski izle. Erişilemezse null → çağıran localStorage'a düşer. */
export function watchYanlislar(uid, callback) {
  if (!db || !uid) { callback([]); return () => {} }
  const q = query(collection(db, 'users', uid, 'yanlislar'), orderBy('createdAt', 'desc'))
  return onSnapshot(q, (snap) => callback(snap.docs.map((d) => ({ id: d.id, ...d.data() }))), () => callback(null))
}

export async function addYanlis(uid, y) {
  if (!db || !uid) return null
  const ref = await addDoc(collection(db, 'users', uid, 'yanlislar'), { ...y, createdAt: serverTimestamp() })
  return ref.id
}

export async function updateYanlis(uid, id, patch) {
  if (!db || !uid) return
  await updateDoc(doc(db, 'users', uid, 'yanlislar', id), { ...patch, updatedAt: serverTimestamp() })
}

export async function removeYanlis(uid, id) {
  if (!db || !uid) return
  await deleteDoc(doc(db, 'users', uid, 'yanlislar', id))
}

// === Bilgi kartları (flashcard — düz model, deste alanıyla gruplu) ===
/** Kartları en yeni→eski izle. Erişilemezse null → çağıran localStorage'a düşer. */
export function watchKartlar(uid, callback) {
  if (!db || !uid) { callback([]); return () => {} }
  const q = query(collection(db, 'users', uid, 'kartlar'), orderBy('createdAt', 'desc'))
  return onSnapshot(q, (snap) => callback(snap.docs.map((d) => ({ id: d.id, ...d.data() }))), () => callback(null))
}

export async function addKart(uid, k) {
  if (!db || !uid) return null
  const ref = await addDoc(collection(db, 'users', uid, 'kartlar'), { ...k, createdAt: serverTimestamp() })
  return ref.id
}

export async function updateKart(uid, id, patch) {
  if (!db || !uid) return
  await updateDoc(doc(db, 'users', uid, 'kartlar', id), { ...patch, updatedAt: serverTimestamp() })
}

export async function removeKart(uid, id) {
  if (!db || !uid) return
  await deleteDoc(doc(db, 'users', uid, 'kartlar', id))
}

// === Günlük çalışma serisi (streak) ===
const SK = 'unisense_streak'
const loadStreak = () => { try { return JSON.parse(localStorage.getItem(SK) || 'null') } catch { return null } }
const saveStreak = (s) => { try { localStorage.setItem(SK, JSON.stringify(s)) } catch { /* noop */ } }

/** Görüntüleme için güncel seri (localStorage anında; girişliyse buluttan tazele). */
export async function getStreak(uid) {
  let s = loadStreak()
  if (uid && db) {
    try {
      const snap = await getDoc(doc(db, 'users', uid, 'aktivite', 'gunluk'))
      if (snap.exists()) { s = snap.data(); saveStreak(s) }
    } catch { /* buluta erişilemedi → localStorage */ }
  }
  return { current: guncelSeri(s), longest: s?.longest || 0 }
}

/** Bugün aktivite işle (konu/deneme). Günde 1 kez yazar; güncel seriyi döner. */
export async function recordActivity(uid) {
  const today = bugunStr()
  if (localStorage.getItem(SK + '_last') === today) return guncelSeri(loadStreak())
  let prev = loadStreak()
  if (uid && db) { try { const snap = await getDoc(doc(db, 'users', uid, 'aktivite', 'gunluk')); if (snap.exists()) prev = snap.data() } catch { /* noop */ } }
  const next = serisiIsle(prev, today)
  saveStreak(next)
  localStorage.setItem(SK + '_last', today)
  if (uid && db && next.changed) {
    setDoc(doc(db, 'users', uid, 'aktivite', 'gunluk'),
      { current: next.current, longest: next.longest, lastDate: next.lastDate, updatedAt: serverTimestamp() },
      { merge: true }).catch(() => {})
  }
  return next.current
}

// === PUSH BİLDİRİM (FCM) — günlük çalışma hatırlatması ===
// VAPID key Firebase Console → Cloud Messaging → Web Push certificates'ten alınır.
// Yoksa (yapılandırılmadıysa) push sessizce devre dışı — UI kartı da görünmez.
const VAPID_KEY = import.meta.env.VITE_FIREBASE_VAPID_KEY

/** Push bu ortamda kullanılabilir mi? (tarayıcı desteği + VAPID key). UI'ı buna göre göster. */
export async function pushAvailable() {
  if (!app || !VAPID_KEY) return false
  try { return await isMessagingSupported() } catch { return false }
}

/**
 * Bildirim izni iste → FCM token al → Firestore'a kaydet. KULLANICI JESTİYLE çağrılmalı
 * (Notification.requestPermission tarayıcı kuralı). Döner: {ok, reason}.
 */
export async function enablePush(uid) {
  if (!app || !db || !uid) return { ok: false, reason: 'no-auth' }
  if (!VAPID_KEY) return { ok: false, reason: 'no-vapid' }
  if (!(await isMessagingSupported().catch(() => false))) return { ok: false, reason: 'unsupported' }
  const perm = await Notification.requestPermission()
  if (perm !== 'granted') return { ok: false, reason: 'denied' }
  // FCM'in kendi SW'sini PUBLIC config ile (query param) kaydet — PWA sw.js'i ile
  // ayrı scope, çakışmaz. SW config'i import.meta.env okuyamadığı için böyle geçilir.
  const swReg = await navigator.serviceWorker.register(
    `/firebase-messaging-sw.js?${new URLSearchParams({
      apiKey: firebaseConfig.apiKey || '',
      projectId: firebaseConfig.projectId || '',
      messagingSenderId: firebaseConfig.messagingSenderId || '',
      appId: firebaseConfig.appId || '',
    }).toString()}`,
  )
  const messaging = getMessaging(app)
  const token = await getToken(messaging, { vapidKey: VAPID_KEY, serviceWorkerRegistration: swReg })
  if (!token) return { ok: false, reason: 'no-token' }
  // Token = doküman ID → aynı cihaz tek kayıt (duplikasyon yok)
  await setDoc(doc(db, 'users', uid, 'pushTokens', token), {
    token,
    ua: (navigator.userAgent || '').slice(0, 300),
    updatedAt: serverTimestamp(),
  }, { merge: true })
  return { ok: true }
}

/** Bu cihazın push kaydını kaldır (bildirimleri kapat). */
export async function disablePush(uid) {
  if (!app || !db || !uid) return
  try {
    if (await isMessagingSupported().catch(() => false)) {
      const messaging = getMessaging(app)
      const token = await getToken(messaging, { vapidKey: VAPID_KEY }).catch(() => null)
      if (token) {
        await deleteDoc(doc(db, 'users', uid, 'pushTokens', token)).catch(() => {})
        await deleteToken(messaging).catch(() => {})
      }
    }
  } catch { /* noop */ }
}

/** Kullanıcının displayName/photoURL'ünü Auth + Firestore'da güncelle. */
export async function updateUserBasicInfo(user, { displayName, photoURL }) {
  if (!auth || !db) throw new Error('Firebase yok')
  const updates = {}
  if (displayName !== undefined) updates.displayName = displayName
  if (photoURL !== undefined) updates.photoURL = photoURL
  if (Object.keys(updates).length > 0) {
    await updateProfile(user, updates)
  }
  await setDoc(
    doc(db, 'users', user.uid),
    { ...updates, updatedAt: serverTimestamp() },
    { merge: true }
  )
}

/** Avatar dosyasını Storage'a yükle ve URL döndür. */
export async function uploadAvatar(uid, file) {
  if (!storage) throw new Error('Firebase Storage yok')
  // Dosya boyutu / format kontrolü
  if (file.size > 5 * 1024 * 1024) {
    throw new Error('Dosya çok büyük (max 5 MB)')
  }
  // storage.rules ile aynı liste — SVG bilerek yok (script gömülebilir)
  const ALLOWED_TYPES = ['image/png', 'image/jpeg', 'image/webp']
  if (!ALLOWED_TYPES.includes(file.type)) {
    throw new Error('Sadece PNG, JPEG veya WebP kabul edilir')
  }
  const ext = (file.name.split('.').pop() || 'png').toLowerCase()
  const ref = storageRef(storage, `avatars/${uid}/avatar-${Date.now()}.${ext}`)
  await uploadBytes(ref, file, { contentType: file.type })
  return await getDownloadURL(ref)
}

/** Şifreyi değiştir (mevcut şifre ile reauthenticate edilir). */
export async function changePassword(currentPassword, newPassword) {
  if (!auth || !auth.currentUser) throw new Error('Giriş yapmamışsın')
  const user = auth.currentUser
  if (!user.email) {
    throw new Error('Şifre değiştirme sadece e-posta hesapları için (Google/diğer için sağlayıcı sayfasından)')
  }
  // Reauthenticate
  const cred = EmailAuthProvider.credential(user.email, currentPassword)
  await reauthenticateWithCredential(user, cred)
  // Şifreyi güncelle
  await updatePassword(user, newPassword)
}

/** Auth provider'ı (Google/Email) tespit et. */
export function getAuthProvider(user) {
  if (!user) return null
  const providers = user.providerData?.map((p) => p.providerId) || []
  if (providers.includes('google.com')) return 'google'
  if (providers.includes('password')) return 'email'
  return providers[0] || 'unknown'
}

// === TERCIH LISTESI ===

export function watchTercihList(uid, callback) {
  if (!db) return () => {}
  const q = query(
    collection(db, 'users', uid, 'tercih'),
    orderBy('order', 'asc'),
    limit(24)
  )
  return onSnapshot(q, (snap) => {
    callback(snap.docs.map((d) => ({ id: d.id, ...d.data() })))
  })
}

export async function addToTercih(uid, dept, order) {
  if (!db) throw new Error('Firebase yok')
  const code = String(dept.department_code || dept.code)
  await setDoc(doc(db, 'users', uid, 'tercih', code), {
    department_code: code,
    department_name: dept.department_name || dept.name,
    university_code: dept.university_code,
    university_name: dept.university_name || dept.universityName,
    city: dept.city || '',
    score_type: dept.score_type || dept.scoreType || null,
    last_year_base_rank: dept.last_year_base_rank ?? null,
    last_year_base_score: dept.last_year_base_score ?? null,
    quota: dept.quota ?? null,
    fit_score: dept.fit_score ?? null,
    safety_level: dept.safety_level || null,
    order,
    addedAt: serverTimestamp(),
  })
}

export async function removeFromTercih(uid, code) {
  if (!db) throw new Error('Firebase yok')
  await deleteDoc(doc(db, 'users', uid, 'tercih', String(code)))
}

/**
 * Tercih item'ına kişisel not yaz (boş string silmek için).
 * Maks 500 karakter UI'da clamp edilir.
 */
export async function updateTercihNote(uid, code, note) {
  if (!db) throw new Error('Firebase yok')
  const trimmed = (note || '').slice(0, 500)
  await updateDoc(doc(db, 'users', uid, 'tercih', String(code)), {
    note: trimmed,
    noteUpdatedAt: serverTimestamp(),
  })
}

/**
 * Tercih listesinin order alanlarını batch olarak yeniden yaz.
 * @param {string} uid
 * @param {Array<{id: string}>} orderedItems - yeni sıraya göre item array'i
 */
export async function reorderTercihList(uid, orderedItems) {
  if (!db) throw new Error('Firebase yok')
  if (!Array.isArray(orderedItems) || orderedItems.length === 0) return
  const batch = writeBatch(db)
  orderedItems.forEach((item, idx) => {
    const ref = doc(db, 'users', uid, 'tercih', String(item.id))
    batch.update(ref, { order: idx + 1 })
  })
  await batch.commit()
}

/**
 * Birden fazla tercih item'ının eksik alanlarını (rank, score, quota, vs)
 * tek seferde Firestore'da güncelle. Backend lookup'ından gelen veri ile.
 */
export async function backfillTercihList(uid, codeToData) {
  if (!db) throw new Error('Firebase yok')
  if (!codeToData || Object.keys(codeToData).length === 0) return
  const batch = writeBatch(db)
  for (const [code, data] of Object.entries(codeToData)) {
    const ref = doc(db, 'users', uid, 'tercih', String(code))
    // sadece null/eksik olabilecek alanları yazıyoruz
    const patch = {}
    if (data.last_year_base_rank != null) patch.last_year_base_rank = data.last_year_base_rank
    if (data.last_year_base_score != null) patch.last_year_base_score = data.last_year_base_score
    if (data.quota != null) patch.quota = data.quota
    if (data.score_type) patch.score_type = data.score_type
    if (data.city) patch.city = data.city
    if (data.university_name) patch.university_name = data.university_name
    if (data.department_name) patch.department_name = data.department_name
    if (Object.keys(patch).length > 0) {
      batch.update(ref, patch)
    }
  }
  await batch.commit()
}

// === KPSS TERCIH LISTESI (YKS tercihinden AYRI alan; merkezi yerleştirmede 30 tercih) ===

export const MAX_KPSS_TERCIH = 30

export function watchKpssTercih(uid, callback) {
  if (!db) return () => {}
  const q = query(
    collection(db, 'users', uid, 'kpss_tercih'),
    orderBy('order', 'asc'),
    limit(MAX_KPSS_TERCIH)
  )
  return onSnapshot(q, (snap) => {
    callback(snap.docs.map((d) => ({ id: d.id, ...d.data() })))
  })
}

export async function addToKpssTercih(uid, kadro, order) {
  if (!db) throw new Error('Firebase yok')
  const code = String(kadro.kadro_kodu)
  await setDoc(doc(db, 'users', uid, 'kpss_tercih', code), {
    kadro_kodu: code,
    kurum: kadro.kurum || '',
    unvan: kadro.unvan || '',
    il: kadro.il || '',
    duzey: kadro.duzey || '',
    puan_turu: kadro.puan_turu || '',
    kontenjan: kadro.kontenjan ?? null,
    gecmis_taban: kadro.gecmis_taban ?? null,
    // Eşleşme + özel koşullar (⚠️) tercih listesinde de gösterilsin (BULGU #24)
    eslesme: kadro.eslesme || '',
    ozel_kosullar: Array.isArray(kadro.ozel_kosullar) ? kadro.ozel_kosullar.slice(0, 3) : [],
    order,
    addedAt: serverTimestamp(),
  })
}

export async function removeFromKpssTercih(uid, code) {
  if (!db) throw new Error('Firebase yok')
  await deleteDoc(doc(db, 'users', uid, 'kpss_tercih', String(code)))
}

/** KPSS/DGS/TUS/DUS/LGS tercih listelerini yeni sıraya göre topluca numarala. */
export async function reorderSubcollection(uid, sub, orderedIds) {
  if (!db || !Array.isArray(orderedIds) || orderedIds.length === 0) return
  const batch = writeBatch(db)
  orderedIds.forEach((id, idx) => {
    batch.update(doc(db, 'users', uid, sub, String(id)), { order: idx + 1 })
  })
  try {
    await batch.commit()
  } catch (e) {
    // Eşzamanlı silmede batch komple reddedilir — sessiz kalmasın; UI zaten
    // onSnapshot'la gerçek duruma döner, kalıcı hasar yok.
    console.warn(`reorder ${sub} başarısız (eşzamanlı değişiklik olabilir):`, e?.message)
  }
}

// === DGS TERCIH LISTESI (üçüncü ayrı alan; DGS merkezi yerleştirmede 30 tercih) ===

export const MAX_DGS_TERCIH = 30

export function watchDgsTercih(uid, callback) {
  if (!db) return () => {}
  const q = query(
    collection(db, 'users', uid, 'dgs_tercih'),
    orderBy('order', 'asc'),
    limit(MAX_DGS_TERCIH)
  )
  return onSnapshot(q, (snap) => {
    callback(snap.docs.map((d) => ({ id: d.id, ...d.data() })))
  })
}

export async function addToDgsTercih(uid, prog, order) {
  if (!db) throw new Error('Firebase yok')
  const code = String(prog.department_code)
  await setDoc(doc(db, 'users', uid, 'dgs_tercih', code), {
    department_code: code,
    program_adi: prog.program_adi || '',
    university_name: prog.university_name || '',
    city: prog.city || '',
    puan_turu: prog.puan_turu || '',
    kontenjan: prog.kontenjan ?? null,
    min_puan: prog.min_puan ?? null,
    order,
    addedAt: serverTimestamp(),
  })
}

export async function removeFromDgsTercih(uid, code) {
  if (!db) throw new Error('Firebase yok')
  await deleteDoc(doc(db, 'users', uid, 'dgs_tercih', String(code)))
}

// === TUS/DUS UZMANLIK TERCIH LISTESI (tus_tercih / dus_tercih — ayrı koleksiyonlar) ===
// TUS ve DUS aynı veri şeklinde olduğu için tek jenerik fonksiyon seti; koleksiyon
// sinav'a göre seçilir. Kişisel kısa liste (resmi yerleştirme ÖSYM'de yapılır).

export const MAX_TUS_TERCIH = 30

const _uzmanlikSub = (sinav) => (sinav === 'DUS' ? 'dus_tercih' : 'tus_tercih')

export function watchUzmanlikTercih(uid, sinav, callback) {
  if (!db) return () => {}
  // limit() BİLEREK yok: sorgu limitli olursa MAX üstüne taşan doküman
  // (ör. eski bir yarış durumundan) kalıcı görünmez ve silinemez olur.
  // Ekleme zaten client'ta MAX ile kapatılıyor.
  const q = query(
    collection(db, 'users', uid, _uzmanlikSub(sinav)),
    orderBy('order', 'asc')
  )
  return onSnapshot(q, (snap) => {
    callback(snap.docs.map((d) => ({ id: d.id, ...d.data() })))
  })
}

export async function addToUzmanlikTercih(uid, sinav, prog, order) {
  if (!db) throw new Error('Firebase yok')
  const code = String(prog.kod)
  await setDoc(doc(db, 'users', uid, _uzmanlikSub(sinav), code), {
    kod: code,
    dal: prog.dal || '',
    kurum: prog.kurum || '',
    kontenjan_turu: prog.kontenjan_turu || '',
    min_puan: prog.min_puan ?? null,
    max_puan: prog.max_puan ?? null,
    kontenjan: prog.kontenjan ?? null,
    yerlesen: prog.yerlesen ?? null,
    order,
    addedAt: serverTimestamp(),
  })
}

export async function removeFromUzmanlikTercih(uid, sinav, code) {
  if (!db) throw new Error('Firebase yok')
  await deleteDoc(doc(db, 'users', uid, _uzmanlikSub(sinav), String(code)))
}

// === LGS LISE TERCIH LISTESI (lgs_tercih) ===
// Liselerin verisinde benzersiz kod yok → okul+ilçe+dil'den kararlı bir anahtar üret.

export const MAX_LGS_TERCIH = 25

export function lgsTercihKey(lise) {
  // yuzdelik anahtara DAHİL: veride aynı okul+ilçe+dil'e sahip farklı program
  // satırları var (kaynak alan/dal sütununu ayrıştırmıyor) — yüzdelik olmadan
  // iki farklı program tek Firestore dokümanına düşüyor ve kartlar birbirine
  // bağlanıyordu (birini ekleyince ikisi de "Listede" görünüyordu).
  const raw = `${lise.okul || ''}-${lise.ilce || ''}-${lise.dil || ''}-${lise.yuzdelik ?? ''}`
  return raw
    .replace(/İ/g, 'i').replace(/I/g, 'i').toLowerCase()
    .replace(/[çğıöşü]/g, (c) => ({ ç: 'c', ğ: 'g', ı: 'i', ö: 'o', ş: 's', ü: 'u' }[c] || c))
    .replace(/[^a-z0-9.]+/g, '-').replace(/^-|-$/g, '')
    .slice(0, 200) || 'lise'
}

export function watchLgsTercih(uid, callback) {
  if (!db) return () => {}
  // limit() bilerek yok — bkz. watchUzmanlikTercih notu
  const q = query(
    collection(db, 'users', uid, 'lgs_tercih'),
    orderBy('order', 'asc')
  )
  return onSnapshot(q, (snap) => {
    callback(snap.docs.map((d) => ({ id: d.id, ...d.data() })))
  })
}

export async function addToLgsTercih(uid, lise, order) {
  if (!db) throw new Error('Firebase yok')
  const key = lgsTercihKey(lise)
  await setDoc(doc(db, 'users', uid, 'lgs_tercih', key), {
    okul: lise.okul || '',
    il: lise.il || '',
    ilce: lise.ilce || '',
    tur: lise.tur || '',
    dil: lise.dil || '',
    yuzdelik: lise.yuzdelik ?? null,
    taban_puan: lise.taban_puan ?? null,
    kontenjan: lise.kontenjan ?? null,
    order,
    addedAt: serverTimestamp(),
  })
}

export async function removeFromLgsTercih(uid, key) {
  if (!db) throw new Error('Firebase yok')
  await deleteDoc(doc(db, 'users', uid, 'lgs_tercih', String(key)))
}

// === QUERY HISTORY (basit log) ===

export async function logQuery(uid, queryText, response) {
  if (!db) return
  try {
    await addDoc(collection(db, 'users', uid, 'queries'), {
      query: queryText,
      response_preview: (response?.text || '').slice(0, 500),
      doc_count: response?.docs?.length || 0,
      latency_ms: response?.total_latency_ms || null,
      ts: serverTimestamp(),
    })
  } catch (e) {
    console.warn('Query log fail', e)
  }
}

// === SOHBET SESSIONS (max 5/kişi) ===

/** Tüm session'ları (en yeni → en eski) gerçek zamanlı izle. */
export function watchSessions(uid, callback) {
  if (!db) return () => {}
  const q = query(
    collection(db, 'users', uid, 'sessions'),
    orderBy('updatedAt', 'desc')
  )
  return onSnapshot(q, (snap) => {
    callback(snap.docs.map((d) => ({ id: d.id, ...d.data() })))
  })
}

/** Tek bir session'ın mesajlarını gerçek zamanlı izle (kronolojik sıra). */
export function watchSessionMessages(uid, sessionId, callback) {
  if (!db || !sessionId) return () => {}
  const q = query(
    collection(db, 'users', uid, 'sessions', sessionId, 'messages'),
    orderBy('createdAt', 'asc')
  )
  return onSnapshot(q, (snap) => {
    callback(snap.docs.map((d) => ({ id: d.id, ...d.data() })))
  })
}

/** Yeni session oluştur. 5'ten fazlaysa en eskiyi sil (FIFO). */
export async function createSession(uid, firstQuery = '') {
  if (!db) throw new Error('Firebase yok')

  // Mevcut session sayısını kontrol et
  const sessionsRef = collection(db, 'users', uid, 'sessions')
  const allSnap = await getDocs(query(sessionsRef, orderBy('updatedAt', 'desc')))

  // Limit aşılırsa en eskiyi sil
  if (allSnap.size >= MAX_SESSIONS_PER_USER) {
    const oldestDocs = allSnap.docs.slice(MAX_SESSIONS_PER_USER - 1)
    for (const d of oldestDocs) {
      await deleteSession(uid, d.id)
    }
  }

  // Yeni session
  const ref = doc(sessionsRef)
  const title = firstQuery.slice(0, 60).trim() || 'Yeni Sohbet'
  await setDoc(ref, {
    title,
    messageCount: 0,
    createdAt: serverTimestamp(),
    updatedAt: serverTimestamp(),
  })
  return ref.id
}

/** Mevcut session'ın başlığını güncelle (ilk mesajdan sonra). */
export async function updateSessionTitle(uid, sessionId, title) {
  if (!db) return
  await updateDoc(doc(db, 'users', uid, 'sessions', sessionId), {
    title: title.slice(0, 60),
    updatedAt: serverTimestamp(),
  })
}

/** Session'a mesaj ekle. */
export async function addSessionMessage(uid, sessionId, message) {
  if (!db || !sessionId) return null
  const messagesRef = collection(db, 'users', uid, 'sessions', sessionId, 'messages')
  const docRef = await addDoc(messagesRef, {
    ...message,
    createdAt: serverTimestamp(),
  })
  // Session'ın updatedAt + messageCount güncelle
  const sessionRef = doc(db, 'users', uid, 'sessions', sessionId)
  const sessionSnap = await getDoc(sessionRef)
  const currentCount = sessionSnap.exists() ? (sessionSnap.data().messageCount || 0) : 0
  await updateDoc(sessionRef, {
    messageCount: currentCount + 1,
    updatedAt: serverTimestamp(),
  })
  return docRef.id
}

/** Session ve içindeki tüm mesajları sil. */
export async function deleteSession(uid, sessionId) {
  if (!db || !sessionId) return
  // Önce mesajları sil (batched)
  const messagesRef = collection(db, 'users', uid, 'sessions', sessionId, 'messages')
  const messagesSnap = await getDocs(messagesRef)

  const batch = writeBatch(db)
  messagesSnap.docs.forEach((m) => batch.delete(m.ref))
  batch.delete(doc(db, 'users', uid, 'sessions', sessionId))
  await batch.commit()
}

/** Mevcut session sayısını al. */
export async function getSessionCount(uid) {
  if (!db) return 0
  const snap = await getDocs(collection(db, 'users', uid, 'sessions'))
  return snap.size
}
