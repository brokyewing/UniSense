# DEVIR - UniSense Frontend Refactoring

## Son Durum
- **Build**: ✅ BAŞARILI (631 URL prerender)
- **Tüm servisler çalışıyor**: Backend (8002), Frontend (5177), ngrok, Firebase Emulators
- **Service Layer**: `src/services/` altına modüler yapı kuruldu

## Tamamlanan Migration'lar

### 1. Service Layer Kurulumu (`src/services/`)
| Dosya | Sorumluluk |
|-------|------------|
| `constants.js` | Limitler, koleksiyon isimleri, eşikler, PRESET_AVATARS — **tek kaynak** |
| `auth.js` | Firebase Auth (login, register, logout, password) |
| `firestore-core.js` | **Jenerik** `watchSubcollection`, CRUD helpers, `app` import |
| `firestore-study.js` | Konu, deneme, soru, yanlış, not, kartlar, istatistik |
| `firestore-prefs.js` | **TÜM tercih listeleri** (YKS/DGS/KPSS/TUS/DUS/LGS) — tek `_watchTercih` pattern |
| `firestore-plan.js` | Planlayıcı, istatistik, streak, sıralama (`siralama*` fonksiyonları dahil) |
| `firestore-push.js` | FCM push, avatar, query log, chat sessions |
| `firestore-user.js` | `ensureUserDoc` (kullanıcı profili oluşturma) |
| `api.js` | Backend API (timeout, auth header, ApiError) |
| `hooks.js` | Tüm custom hook'lar (20+ hook) |
| `index.js` | Barrel export |

### 2. Component Migration'ları (16 sayfa + 3 component + 3 lib + 1 context)
**Sayfalar:**
Search, Recommend, Calisma, Deneme, Konular, Planim, TercihList, Hesap, Ozetler, Notlar, Pano, LGS, Siralama, Pusula, Profile, TusDus

**Component'ler:**
- PushOptIn.jsx, StreakBadge.jsx, ChatSidebar.jsx

**Lib'ler:**
- usage.js, api.js

**Context'ler:**
- AuthContext.jsx

### 3. Build & Deploy
- ✅ Build başarılı - 631 URL prerender
- ✅ Chunk splitting çalışıyor (react-vendor, three-vendor, firebase-vendor, ui-vendor)
- ✅ Vite proxy `/api` → `localhost:8002` çalışıyor
- ✅ ngrok tunnel aktif: `https://75ce-88-227-34-121.ngrok-free.app`
- ✅ Firebase Emulators: Firestore (8085), Auth (9099), UI (4000)

## Kalan İşler
1. **Chunk boyutu**: `three-vendor` (857 kB) ve `firebase-vendor` (520 kB) büyük - code-splitting iyileştirilebilir
2. **Legacy firebase.js**: Sadece `app` ve `auth` core instance'ları için kullanılıyor (service layer'ın temeli)

## Sıradaki Adım
- Chunk splitting optimizasyonu (dynamic import ile code-split)
- `firebase.js`'i tamamen ortadan kaldırmak (app/auth instance'larını service layer'a taşımak)

## Bloker
- Yok - tüm servisler sağlıklı