# GOREVLER - UniSense Frontend Refactoring

## ✅ Tamamlananlar

### Service Layer (`src/services/`)
- [x] `firebase-init.js` - Firebase app/auth/db/storage init — **tek kaynak**
- [x] `constants.js` - Limitler, koleksiyon isimleri, eşikler, PRESET_AVATARS
- [x] `auth.js` - Firebase Auth
- [x] `firestore-core.js` - Jenerik CRUD + `watchSubcollection`, `db` import
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
- [x] Chunk splitting optimize edildi (9 ayrı chunk)
- [x] Vite proxy + ngrok + Firebase Emulators çalışıyor

### Legacy Cleanup
- [x] `firebase.js` (1068 satır) tamamen silindi
- [x] `firebase-init.js` oluşturuldu
- [x] Tüm `../firebase` importları service layer'a taşındı
- [x] `PRESET_AVATARS` → `constants.js`
- [x] `siralama*` fonksiyonları → `firestore-plan.js`
- [x] `@vercel/analytics` kuruldu

### Temizlik
- [x] `TercihListYKSContent.jsx` silindi
- [x] `fix_tercih.ps1` / `fix_end.ps1` silindi

## 🔄 Devam Eden / Sıradaki

### Chunk Size Optimizasyonu (Kalan)
- [ ] `three-core` (688 kB) - dynamic import ile code-split (lazy loading)

### Test Coverage
- [ ] Service layer için unit test'ler

### TypeScript Migration (Uzun Vadeli)
- [ ] JS → TS migration

## 📋 Notlar
- `constants.js`'e `MAX_DGS_TERCIH`, `MAX_KPSS_TERCIH`, `MAX_TUS_TERCIH`, `MAX_LGS_TERCIH`, `PRESET_AVATARS` exportları eklendi
- `firestore-core.js` duplicate export hatası düzeltildi
- `hooks.js` tüm gerekli hook'ları içeriyor
- Dynamic import pattern: `import('@/services/firestore-prefs').then(m => m.addToDgsTercih(...))`
- Build: `npm run build` → 631 URL prerender, 0 hata
- Legacy firebase imports: 0 (sadece service layer içinde `firebase-init.js` import edilir)