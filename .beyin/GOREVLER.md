# GOREVLER - UniSense Ekstra Özellikler

## ✅ Tamamlananlar

### PWA / Offline Destek
- [x] `manifest.webmanifest` - app name, icons, theme color, display: standalone
- [x] Service worker (`sw.js`) - network-first caching, offline fallback
- [x] `index.html` - manifest link, meta tags, theme-color
- [x] Service worker registration (`main.jsx`)
- [x] `PWAInstallPrompt.jsx` - custom "Ana ekrana ekle" prompt

### Error Boundary
- [x] `ErrorBoundary.jsx` - class component with getDerivedStateFromError
- [x] Wrapped entire app in ErrorBoundary (main.jsx)
- [x] User-friendly error UI with retry and reload buttons
- [x] Error details in dev mode only

### Bölüm Karşılaştırma (Side-by-Side)
- [x] Compare.jsx sayfası mevcut (25+ metrik karşılaştırma)
- [x] AI destekli karşılaştırma özeti eklendi
- [ ] Tercih listesinden "Karşılaştır" butonu ekle

### Tercih Sırası Optimizasyonu
- [x] AI destekli tercih sıralama önerisi (TercihList.jsx)
- [x] "Analiz Et" butonu ve sonuç gösterimi
- [ ] Risk analizi (güvenli/hedef/riskli dağılımı) UI

### Push Notification Backend
- [x] `push_service.py` - FCM push notification service (firebase-admin)
- [x] API endpoints: `/push/send`, `/push/exam-reminder`, `/push/streak-reminder`
- [x] `firebase-admin` added to requirements.txt
- [ ] Service account key setup (Firebase Console)
- [ ] Scheduled jobs (cron) for periodic notifications
- [ ] Frontend integration (call backend endpoints)

### Unit Test Coverage
- [x] Vitest 2.1.0 kurulumu
- [x] `vitest.config.js` - jsdom environment
- [x] `test/setup.js` - cleanup
- [x] `constants.test.js` - 12 test
- [x] `api.test.js` - 2 test
- [x] `test` ve `test:watch` scripts
- [ ] Service layer (hooks, firestore-*) için test'ler
- [ ] Component test'leri (React Testing Library)

### Service Layer Migration (Önceki)
- [x] Tüm 16 sayfa + 3 component + 3 lib + 1 context migrate edildi
- [x] `firebase.js` tamamen kaldırıldı
- [x] Chunk splitting optimize edildi
- [x] Build: 631 URL prerender, 0 hata

## 🔄 Devam Eden / Sıradaki

### Burs/Ücret Veritabanı (Yüksek Zorluk)
- [ ] Backend: burs/ücret veri modeli + API endpoint
- [ ] Frontend: burs bilgisi gösterimi (Hesap/Öneriler sayfalarında)
- [ ] Her sene güncellenecek şekilde veri yapısı (yıl bazlı)
- [ ] Vakıf üniversiteleri burs oranları

### Mezun İstihdam Verisi (Yüksek Zorluk)
- [ ] Backend: TÜİK/İŞKUR veri entegrasyonu
- [ ] Frontend: bölüm sayfasında istihdam bilgisi
- [ ] İş bulma oranı, maaş aralığı, istihdam sektörü

### Analytics Dashboard (Yüksek Zorluk)
- [ ] Kullanıcı davranış analizi
- [ ] Admin paneli (basit)

### TypeScript Migration (Uzun Vadeli)
- [ ] JS → TS migration (uzun vadeli)
- [ ] Tip tanımları
- [ ] Gradual migration (sayfa sayfa)

## 📋 Notlar
- Tüm özellikler ücretsiz olacak (premium kaldırıldı)
- Her özellik için build test + GitHub push yapılacak
- PWA + Error Boundary + Compare AI + Tercih Optimization + Unit Tests + Push Backend tamamlandı
- Push notification: backend endpoint'ler hazır, Firebase Admin SDK + service account key gerekli
- Burs/Ücret, İstihdam, Analytics: büyük feature'lar, veri kaynağı gerekli