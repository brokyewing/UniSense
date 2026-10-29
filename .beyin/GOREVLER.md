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

### Service Layer Migration (Önceki)
- [x] Tüm 16 sayfa + 3 component + 3 lib + 1 context migrate edildi
- [x] `firebase.js` tamamen kaldırıldı
- [x] Chunk splitting optimize edildi
- [x] Build: 631 URL prerender, 0 hata

## 🔄 Devam Eden / Sıradaki

### 1. Bölüm Karşılaştırma (Side-by-Side) — Zaten Mevcut
- [x] Compare.jsx sayfası mevcut (25+ metrik karşılaştırma)
- [ ] AI destekli karşılaştırma özeti ekle
- [ ] Tercih listesinden "Karşılaştır" butonu ekle
- [ ] Test + deploy

### 2. Tercih Sırası Optimizasyonu
- [ ] AI destekli tercih sıralama önerisi
- [ ] "Bu sıralamayla en iyi strateji şu" mesajı
- [ ] Risk analizi (güvenli/hedef/riskli dağılımı)
- [ ] Test + deploy

### 3. Unit Test Coverage
- [ ] Vitest kurulumu
- [ ] Service layer test'leri
- [ ] Component test'leri (React Testing Library)
- [ ] CI/CD'de test çalıştırma

### 4. Push Notification Backend
- [ ] Firebase Admin SDK kurulumu (backend)
- [ ] Push notification endpoint
- [ ] Sınav tarihi hatırlatma (scheduled job)
- [ ] Tercih dönemi başladığında push bildirim

### 5. Burs/Ücret Veritabanı
- [ ] Backend: burs/ücret veri modeli + API endpoint
- [ ] Frontend: burs bilgisi gösterimi
- [ ] Her sene güncellenecek şekilde veri yapısı (yıl bazlı)
- [ ] Vakıf üniversiteleri burs oranları

### 6. Mezun İstihdam Verisi
- [ ] Backend: TÜİK/İŞKUR veri entegrasyonu
- [ ] Frontend: bölüm sayfasında istihdam bilgisi
- [ ] İş bulma oranı, maaş aralığı, istihdam sektörü

### 7. Analytics Dashboard
- [ ] Kullanıcı davranış analizi
- [ ] Admin paneli (basit)

### 8. TypeScript Migration (Uzun Vadeli)
- [ ] JS → TS migration (uzun vadeli)
- [ ] Tip tanımları
- [ ] Gradual migration (sayfa sayfa)

## 📋 Notlar
- Tüm özellikler ücretsiz olacak (premium kaldırıldı)
- Her özellik için build test + GitHub push yapılacak
- PWA + Error Boundary tamamlandı
- Compare.jsx zaten mevcut ve kapsamlı (25+ metrik)