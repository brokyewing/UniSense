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

### Component Migrations (16 sayfa)
- [x] **Search.jsx** - `useTercihList`, `useSessionMessages`, `useToast`, `api.ask`
- [x] **Recommend.jsx** - `useTercihList`, `useDgsTercih`, `useKpssTercih`, `useToast`, `api.recommend`, `api.dgsProgramlar`, `api.kpssKadrolar`, `api.dgsGecis`
- [x] **Calisma.jsx** - `useKonuIlerleme`, `useDenemeler`, `useSoruKayit`, `usePlanGorevler`
- [x] **Deneme.jsx** - `useDenemeler`, `useSoruKayit`, `useKonuIlerleme`, `api.konular`
- [x] **Konular.jsx** - `useKonuIlerleme`, `api.konular`
- [x] **Planim.jsx** - `usePlanConfig`, `usePlanGorevler`, `useKonuIlerleme`, `useSoruKayit`, `useIstatistik`, `usePomodoro`
- [x] **TercihList.jsx** - `useTercihList`, `useDgsTercih`, `useKpssTercih`, `useUzmanlikTercih`, `useLgsTercih`
- [x] **Hesap.jsx** - `useUserProfile`, hesap makinesi API
- [x] **Ozetler.jsx** - `useUserProfile`, `api.ozetKartlar`
- [x] **Notlar.jsx** - `useNotlar`
- [x] **Pano.jsx** - `useIstatistik`, `usePomodoro`, `useEmailReminders`, `useUserProfile`
- [x] **LGS.jsx** - `useUserProfile`, `api.lgs` endpoints
- [x] **Siralama.jsx** - `useIstatistik`, `siralama*` (legacy firebase)
- [x] **Pusula.jsx** - `useUserProfile`
- [x] **Profile.jsx** - `useIstatistik`, `useUserProfile`
- [x] **TusDus.jsx** - `useUserProfile`

### Build & Deploy
- [x] Build başarılı (631 URL prerender)
- [x] Chunk splitting optimize edildi
- [x] Vite proxy + ngrok + Firebase Emulators çalışıyor

## 🔄 Devam Eden / Sıradaki

### Component Migrations (Kalan)
- [ ] **BolumDetay.jsx** - `../firebase` importları
- [ ] **BolumKatalog.jsx** - `../firebase` importları
- [ ] **Compare.jsx** - `../firebase` importları
- [ ] **Kariyer.jsx** - `../firebase` importları
- [ ] **Login.jsx** - `../firebase` importları
- [ ] **OzetDetay.jsx** - `../firebase` importları
- [ ] **Privacy.jsx** - `../firebase` importları
- [ ] **Takvim.jsx** - `../firebase` importları

### Legacy Import Cleanup
- [ ] `Profile.jsx` - `PRESET_AVATARS` → service layer'a taşı
- [ ] `Siralama.jsx` - `siralama*` fonksiyonlarını `firestore-push.js`'e taşı

### Test Dosyaları Temizliği
- [ ] `TercihListYKSContent.jsx` - kullanılmıyor, silinebilir
- [ ] `fix_tercih.ps1` - geçici script, silinebilir
- [ ] `fix_end.ps1` - geçici script, silinebilir

### Chunk Size Optimizasyonu
- [ ] `three-vendor` (857 kB) - dynamic import ile code-split
- [ ] `firebase-vendor` (520 kB) - dynamic import ile code-split

## 📋 Notlar
- `constants.js`'e `MAX_DGS_TERCIH`, `MAX_KPSS_TERCIH`, `MAX_TUS_TERCIH`, `MAX_LGS_TERCIH` exportları eklendi
- `firestore-core.js` duplicate export hatası düzeltildi
- `hooks.js` tüm gerekli hook'ları içeriyor
- Dynamic import pattern: `import('@/services/firestore-prefs').then(m => m.addToDgsTercih(...))`
- Build: `npm run build` → 631 URL prerender, 0 hata