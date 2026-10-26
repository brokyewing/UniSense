# GOREVLER - UniSense Frontend Refactoring

## ✅ Tamamlananlar

### Service Layer (`src/services/`)
- [x] `constants.js` - Limitler, koleksiyon isimleri, eşikler, PRESET_AVATARS
- [x] `auth.js` - Firebase Auth
- [x] `firestore-core.js` - Jenerik CRUD + `watchSubcollection`, `app` import
- [x] `firestore-study.js` - Konu, deneme, soru, yanlış, not, kartlar
- [x] `firestore-prefs.js` - TÜM tercih listeleri (tek `_watchTercih` pattern)
- [x] `firestore-plan.js` - Planlayıcı, istatistik, streak, sıralama
- [x] `firestore-push.js` - FCM push, avatar, query log, chat sessions
- [x] `firestore-user.js` - `ensureUserDoc`
- [x] `api.js` - Backend API client
- [x] `hooks.js` - Tüm custom hook'lar
- [x] `index.js` - Barrel export

### Component Migrations (16 sayfa + 3 component + 3 lib + 1 context)
- [x] **Search.jsx**, **Recommend.jsx**, **Calisma.jsx**, **Deneme.jsx**, **Konular.jsx**
- [x] **Planim.jsx**, **TercihList.jsx**, **Hesap.jsx**, **Ozetler.jsx**, **Notlar.jsx**
- [x] **Pano.jsx**, **LGS.jsx**, **Siralama.jsx**, **Pusula.jsx**, **Profile.jsx**, **TusDus.jsx**
- [x] **PushOptIn.jsx**, **StreakBadge.jsx**, **ChatSidebar.jsx**
- [x] **usage.js**, **api.js**, **AuthContext.jsx**

### Build & Deploy
- [x] Build başarılı (631 URL prerender)
- [x] Chunk splitting optimize edildi
- [x] Vite proxy + ngrok + Firebase Emulators çalışıyor

### Temizlik
- [x] `TercihListYKSContent.jsx` silindi
- [x] `fix_tercih.ps1` / `fix_end.ps1` silindi
- [x] `@vercel/analytics` kuruldu

## 🔄 Devam Eden / Sıradaki

### Chunk Size Optimizasyonu
- [ ] `three-vendor` (857 kB) - dynamic import ile code-split
- [ ] `firebase-vendor` (520 kB) - dynamic import ile code-split

### Legacy Cleanup
- [ ] `firebase.js`'i tamamen ortadan kaldırmak (app/auth instance'larını service layer'a taşımak)

## 📋 Notlar
- `constants.js`'e `MAX_DGS_TERCIH`, `MAX_KPSS_TERCIH`, `MAX_TUS_TERCIH`, `MAX_LGS_TERCIH`, `PRESET_AVATARS` exportları eklendi
- `firestore-core.js` duplicate export hatası düzeltildi
- `hooks.js` tüm gerekli hook'ları içeriyor
- Dynamic import pattern: `import('@/services/firestore-prefs').then(m => m.addToDgsTercih(...))`
- Build: `npm run build` → 631 URL prerender, 0 hata
- Legacy firebase imports: sadece `services/auth.js` ve `services/firestore-core.js` (app/auth core instance'ları)