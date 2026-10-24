# DEVIR - UniSense Frontend Refactoring

## Son Durum
- **Build**: ✅ BAŞARILI (631 URL prerender)
- **Tüm servisler çalışıyor**: Backend (8002), Frontend (5177), ngrok, Firebase Emulators
- **Service Layer**: `src/services/` altına modüler yapı kuruldu

## Tamamlanan Migration'lar

### 1. Service Layer Kurulumu (`src/services/`)
| Dosya | Sorumluluk |
|-------|------------|
| `constants.js` | Limitler, koleksiyon isimleri, eşikler — **tek kaynak** |
| `auth.js` | Firebase Auth (login, register, logout, password) |
| `firestore-core.js` | **Jenerik** `watchSubcollection`, CRUD helpers |
| `firestore-study.js` | Konu, deneme, soru, yanlış, not, kartlar, istatistik |
| `firestore-prefs.js` | **TÜM tercih listeleri** (YKS/DGS/KPSS/TUS/DUS/LGS) — tek `_watchTercih` pattern |
| `firestore-plan.js` | Planlayıcı, istatistik, streak, sıralama |
| `firestore-push.js` | FCM push, avatar, query log, chat sessions |
| `api.js` | Backend API (timeout, auth header, ApiError) |
| `hooks.js` | `useTercihList`, `useDgsTercih`, `useKpssTercih`, `useKonuIlerleme`, `useDenemeler`, `useSoruKayit`, `usePlanGorevler`, `useToast`, `useAsync`, `usePomodoro`, `useIstatistik`, `useEmailReminders`, `useUserProfile`, `usePlanConfig` |
| `index.js` | Barrel export |

### 2. Component Migration'ları
| Component | Durum | Kullanılan Hook'lar |
|-----------|-------|---------------------|
| **Search.jsx** | ✅ Tamamlandı | `useTercihList`, `useSessionMessages`, `useToast`, `api.ask` |
| **Recommend.jsx** | ✅ Tamamlandı | `useTercihList`, `useDgsTercih`, `useKpssTercih`, `useToast`, `api.recommend`, `api.dgsProgramlar`, `api.kpssKadrolar` |
| **Calisma.jsx** | ⏳ Sıradaki | `useKonuIlerleme`, `useDenemeler`, `useSoruKayit`, `usePlanGorevler` |
| **TercihList.jsx** | ⏳ Bekliyor | `useTercihList`, `useDgsTercih`, `useKpssTercih`, `useUzmanlikTercih`, `useLgsTercih` |
| **Hesap.jsx** | ⏳ Bekliyor | `useUserProfile`, `api` hesap makinesi endpoints |

### 3. Build & Deploy
- ✅ Build başarılı - 631 URL prerender
- ✅ Chunk splitting çalışıyor (react-vendor, three-vendor, firebase-vendor, ui-vendor)
- ✅ Vite proxy `/api` → `localhost:8002` çalışıyor
- ✅ ngrok tunnel aktif: `https://75ce-88-227-34-121.ngrok-free.app`
- ✅ Firebase Emulators: Firestore (8085), Auth (9099), UI (4000)

## Sıradaki Adım
**Calisma.jsx** migration - `useKonuIlerleme`, `useDenemeler`, `useSoruKayit`, `usePlanGorevler` hook'larını kullanacak şekilde refactor.

## Bloker
- Yok - tüm servisler sağlıklı