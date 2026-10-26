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
| `hooks.js` | Tüm custom hook'lar (`useTercihList`, `useIstatistik`, `useUserProfile`, `usePomodoro`, `useEmailReminders`, `useNotlar`, `useKonuIlerleme`, `useDenemeler`, `useSoruKayit`, `usePlanConfig`, `usePlanGorevler`, `useToast`, `useAsync`, `useDebounce`, `useLocalStorage`, `useSessionStorage`, `useIntersectionObserver`, `useMediaQuery`, `useSubcollection`, `useSessions`, `useSessionMessages`) |
| `index.js` | Barrel export |

### 2. Component Migration'ları (12 sayfa)
| Component | Durum | Kullanılan Hook'lar |
|-----------|-------|---------------------|
| **Search.jsx** | ✅ Tamamlandı | `useTercihList`, `useSessionMessages`, `useToast`, `api.ask` |
| **Recommend.jsx** | ✅ Tamamlandı | `useTercihList`, `useDgsTercih`, `useKpssTercih`, `useToast`, `api.recommend`, `api.dgsProgramlar`, `api.kpssKadrolar`, `api.dgsGecis` |
| **Calisma.jsx** | ✅ Tamamlandı | `useKonuIlerleme`, `useDenemeler`, `useSoruKayit`, `usePlanGorevler` |
| **Deneme.jsx** | ✅ Tamamlandı | `useDenemeler`, `useSoruKayit`, `useKonuIlerleme`, `api.konular` |
| **Konular.jsx** | ✅ Tamamlandı | `useKonuIlerleme`, `api.konular` |
| **Planim.jsx** | ✅ Tamamlandı | `usePlanConfig`, `usePlanGorevler`, `useKonuIlerleme`, `useSoruKayit`, `useIstatistik`, `usePomodoro` |
| **TercihList.jsx** | ✅ Tamamlandı | `useTercihList`, `useDgsTercih`, `useKpssTercih`, `useUzmanlikTercih`, `useLgsTercih` |
| **Hesap.jsx** | ✅ Tamamlandı | `useUserProfile`, `api.hesap` endpoints |
| **Ozetler.jsx** | ✅ Tamamlandı | `useUserProfile`, `api.ozetKartlar` |
| **Notlar.jsx** | ✅ Tamamlandı | `useNotlar` |
| **Pano.jsx** | ✅ Tamamlandı | `useIstatistik`, `usePomodoro`, `useEmailReminders`, `useUserProfile` |
| **LGS.jsx** | ✅ Tamamlandı | `useUserProfile`, `api.lgs` endpoints |
| **Siralama.jsx** | ✅ Tamamlandı | `useIstatistik`, `siralama*` (legacy firebase) |
| **Pusula.jsx** | ✅ Tamamlandı | `useUserProfile` |
| **Profile.jsx** | ✅ Tamamlandı | `useIstatistik`, `useUserProfile` |
| **TusDus.jsx** | ✅ Tamamlandı | `useUserProfile` |

### 3. Build & Deploy
- ✅ Build başarılı - 631 URL prerender
- ✅ Chunk splitting çalışıyor (react-vendor, three-vendor, firebase-vendor, ui-vendor)
- ✅ Vite proxy `/api` → `localhost:8002` çalışıyor
- ✅ ngrok tunnel aktif: `https://75ce-88-227-34-121.ngrok-free.app`
- ✅ Firebase Emulators: Firestore (8085), Auth (9099), UI (4000)

## Kalan İşler
1. **Legacy Firebase Imports**: `Profile.jsx` (`PRESET_AVATARS`) ve `Siralama.jsx` (`siralama*`) - bu sabitler/fonksiyonlar henüz service layer'a taşınmadı
2. **Diğer Sayfalar**: `BolumDetay.jsx`, `BolumKatalog.jsx`, `Compare.jsx`, `Kariyer.jsx`, `Login.jsx`, `OzetDetay.jsx`, `Privacy.jsx`, `Takvim.jsx` - henüz incelenmedi
3. **Test dosyaları**: `TercihListYKSContent.jsx`, `fix_tercih.ps1`, `fix_end.ps1` - temizlenebilir
4. **Chunk boyutu**: `three-vendor` (857 kB) ve `firebase-vendor` (520 kB) büyük - code-splitting iyileştirilebilir

## Sıradaki Adım
1. Kalan sayfaları (`BolumDetay`, `BolumKatalog`, `Compare`, `Kariyer`, `Login`, `OzetDetay`, `Privacy`, `Takvim`) service layer'a migrate et
2. `siralama*` fonksiyonlarını `firestore-push.js`'e taşı
3. Test dosyalarını temizle
4. Chunk splitting optimizasyonu

## Bloker
- Yok - tüm servisler sağlıklı