# GOREVLER - UniSense Frontend Refactoring

## ✅ Tamamlananlar

### Service Layer (`src/services/`)
- [x] `constants.js` - Limitler, koleksiyon isimleri, eşikler
- [x] `auth.js` - Firebase Auth
- [x] `firestore-core.js` - Jenerik CRUD + `watchSubcollection`
- [x] `firestore-study.js` - Konu, deneme, soru, yanlış, not, kartlar
- [x] `firestore-prefs.js` - TÜM tercih listeleri (tek `_watchTercih` pattern)
- [x] `firestore-plan.js` - Planlayıcı, istatistik, streak, sıralama
- [x] `firestore-push.js` - FCM push, avatar, query log, chat sessions
- [x] `api.js` - Backend API client
- [x] `hooks.js` - Tüm custom hook'lar
- [x] `index.js` - Barrel export

### Component Migrations
- [x] **Search.jsx** - `useTercihList`, `useSessionMessages`, `useToast`, `api.ask`
- [x] **Recommend.jsx** - `useTercihList`, `useDgsTercih`, `useKpssTercih`, `useToast`, `api.recommend`, `api.dgsProgramlar`, `api.kpssKadrolar`, `api.dgsGecis`

### Build & Deploy
- [x] Build başarılı (631 URL prerender)
- [x] Chunk splitting optimize edildi
- [x] Vite proxy + ngrok + Firebase Emulators çalışıyor

## 🔄 Devam Eden / Sıradaki

### Component Migrations (Sıralı)
- [ ] **Calisma.jsx** - `useKonuIlerleme`, `useDenemeler`, `useSoruKayit`, `usePlanGorevler`
- [ ] **TercihList.jsx** - `useTercihList`, `useDgsTercih`, `useKpssTercih`, `useUzmanlikTercih`, `useLgsTercih`
- [ ] **Hesap.jsx** - `useUserProfile`, hesap makinesi API
- [ ] **Konular.jsx** - `useKonuIlerleme`, `api.konular`
- [ ] **Deneme.jsx** - `useDenemeler`, `useSoruKayit`, `useKonuIlerleme`, `api.dgsProgramlar`, `api.kpssKadrolar`, `api.dgsGecis`
- [ ] **Planim.jsx** - `usePlanConfig`, `usePlanGorevler`, `useKonuIlerleme`, `useSoruKayit`, `useIstatistik`, `usePomodoro`
- [ ] **Ozetler.jsx** - `useUserProfile`, `api.ozetKartlar`
- [ ] **Notlar.jsx** - `useNotlar`
- [ ] **Pano.jsx** - `useIstatistik`, `usePomodoro`, `useEmailReminders`, `useUserProfile`

### Hook'lar (hooks.js'e eklendi)
- [x] `useTercihList`, `useDgsTercih`, `useKpssTercih`, `useLgsTercih`, `useUzmanlikTercih`
- [x] `useKonuIlerleme`, `useDenemeler`, `useSoruKayit`, `useYanlislar`, `useNotlar`, `useKartlar`
- [x] `usePlanGorevler`, `usePlanConfig`
- [x] `useSessions`, `useSessionMessages`
- [x] `useToast`, `useDebounce`, `useLocalStorage`, `useSessionStorage`, `useAsync`, `useIntersectionObserver`, `useMediaQuery`
- [x] `usePlanConfig`, `useIstatistik`, `usePomodoro`, `useEmailReminders`, `useUserProfile`

## 📋 Notlar
- `constants.js`'e `MAX_DGS_TERCIH`, `MAX_KPSS_TERCIH`, `MAX_TUS_TERCIH`, `MAX_LGS_TERCIH` exportları eklendi
- `firestore-core.js` duplicate export hatası düzeltildi
- `hooks.js` tüm gerekli hook'ları içeriyor
- Dynamic import pattern: `import('@/services/firestore-prefs').then(m => m.addToDgsTercih(...))`