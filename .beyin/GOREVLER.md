# GOREVLER - UniSense Ekstra Özellikler

## 📋 Yapılacaklar (Sıralı)

### 1. PWA / Offline Destek
- [ ] `manifest.json` oluştur (app name, icons, theme color, display: standalone)
- [ ] Service worker (`sw.js`) oluştur (cache strategy: cache-first for assets, network-first for API)
- [ ] `index.html`'e manifest link ve meta tags ekle
- [ ] Vite config'de service worker build desteği
- [ ] "Ana ekrana ekle" prompt'u (beforeinstallprompt event)
- [ ] Offline fallback sayfası
- [ ] Build test + deploy

### 2. Bildirim Sistemi (Push)
- [ ] FCM token yönetimi (zaten var - firestore-push.js)
- [ ] Bildirim izni isteme UI (PushOptIn component var)
- [ ] Sınav tarihi hatırlatma (backend scheduled job)
- [ ] Tercih dönemi başladığında push bildirim
- [ ] Bildirim tercihleri (hangi bildirimler açık/kapalı)
- [ ] Backend: push notification endpoint
- [ ] Test + deploy

### 3. Bölüm Karşılaştırma (Side-by-Side)
- [ ] Compare.jsx sayfası iyileştirme (zaten var, geliştirilecek)
- [ ] 2-3 bölümü yan yana karşılaştırma UI
- [ ] Puan, kontenjan, şehir, iş imkanı karşılaştırma
- [ ] AI destekli karşılaştırma özeti
- [ ] Test + deploy

### 4. Tercih Sırası Optimizasyonu
- [ ] AI destekli tercih sıralama önerisi
- [ ] "Bu sıralamayla en iyi strateji şu" mesajı
- [ ] Risk analizi (güvenli/hedef/riskli dağılımı)
- [ ] Test + deploy

### 5. Burs/Ücret Veritabanı
- [ ] Backend: burs/ücret veri modeli + API endpoint
- [ ] Frontend: burs bilgisi gösterimi (Hesap/Öneriler sayfalarında)
- [ ] Her sene güncellenecek şekilde veri yapısı (yıl bazlı)
- [ ] Vakıf üniversiteleri burs oranları
- [ ] Test + deploy

### 6. Mezun İstihdam Verisi
- [ ] Backend: TÜİK/İŞKUR veri entegrasyonu
- [ ] Frontend: bölüm sayfasında istihdam bilgisi
- [ ] İş bulma oranı, maaş aralığı, istihdam sektörü
- [ ] Test + deploy

### 7. Unit Test Coverage
- [ ] Service layer (hooks, firestore-*) için test'ler
- [ ] Vitest kurulumu
- [ ] Component test'leri (React Testing Library)
- [ ] CI/CD'de test çalıştırma

### 8. TypeScript Migration
- [ ] JS → TS migration (uzun vadeli)
- [ ] Tip tanımları
- [ ] Gradual migration (sayfa sayfa)

### 9. Error Boundary
- [ ] React error boundary component
- [ ] Crash recovery UI
- [ ] Hata raporlama (Sentry veya benzeri)

### 10. Analytics Dashboard
- [ ] Kullanıcı davranış analizi
- [ ] Hangi sayfalar, hangi sorular
- [ ] Admin paneli (basit)

## 📋 Notlar
- Tüm özellikler ücretsiz olacak (premium kaldırıldı)
- Her özellik için build test + GitHub push yapılacak
- Sıralı ilerleme: her biri tamamlandıktan sonra sıradakine geçilecek