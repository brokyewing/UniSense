# GOREVLER - UniSense Ekstra Özellikler

## ✅ Tamamlananlar

### PWA / Offline Destek
- [x] `manifest.webmanifest` - app name, icons, theme color, display: standalone
- [x] Service worker (`sw.js`) - network-first caching, offline fallback
- [x] `index.html` - manifest link, meta tags, theme-color
- [x] Service worker registration (`main.tsx`)
- [x] `PWAInstallPrompt.tsx` - custom "Ana ekrana ekle" prompt

### Error Boundary
- [x] `ErrorBoundary.tsx` - class component with getDerivedStateFromError
- [x] Wrapped entire app in ErrorBoundary (main.tsx)
- [x] User-friendly error UI with retry and reload buttons
- [x] Error details in dev mode only

### Bölüm Karşılaştırma (Side-by-Side)
- [x] Compare.tsx sayfası mevcut (25+ metrik karşılaştırma)
- [x] AI destekli karşılaştırma özeti eklendi
- [x] Burs/Ücret ve İstihdam bilgisi Compare.tsx'e eklendi
- [x] Tercih listesinden "Karşılaştır" butonu ekle (Compare.tsx'e yönlendirme)

### Tercih Sırası Optimizasyonu
- [x] AI destekli tercih sıralama önerisi (TercihList.tsx)
- [x] "Analiz Et" butonu ve sonuç gösterimi
- [x] Risk analizi (güvenli/hedef/riskli dağılımı) UI (TercihList.tsx)

### Push Notification Backend
- [x] `push_service.py` - FCM push notification service (firebase-admin)
- [x] API endpoints: `/push/send`, `/push/exam-reminder`, `/push/streak-reminder`
- [x] `firebase-admin` added to requirements.txt
- [x] Scheduled jobs (daily 09:00 UTC push notification loop)
- [x] Service account key setup (Firebase Console) — completed, firebase-admin initialized successfully
- [x] Push notification service implemented (send_push_notification, send_exam_reminder, send_streak_reminder)
- [x] Frontend integration (call backend endpoints) - pushSend, pushExamReminder, pushStreakReminder added to api.ts

### Unit Test Coverage
- [x] Vitest 2.1.0 kurulumu
- [x] `vitest.config.js` - jsdom environment
- [x] `test/setup.js` - cleanup
- [x] `constants.test.js` - 12 test
- [x] `api.test.js` - 2 test
- [x] `test` ve `test:watch` scripts
- [x] Service layer (hooks, firestore-*) için test'ler - riskLevels, konu, tekrar, oyun test'leri (46 test)
- [x] Component test'leri (React Testing Library) - ErrorBoundary, StreakBadge (4 test)

### Burs/Ücret Veritabanı
- [x] `scholarship.py` model (ScholarshipInfo, ScholarshipListResponse)
- [x] `scholarship_service.py` (list, by_program, years - yıl bazlı)
- [x] `scholarship_data.json` (2026 data, sample vakıf/devlet programlar)
- [x] API endpoints: `/scholarship/list`, `/scholarship/program/{code}`, `/scholarship/years`
- [x] Frontend API: `api.scholarshipList`, `api.scholarshipByProgram`, `api.scholarshipYears`
- [x] Frontend UI (burs bilgisi Compare.tsx'te gösteriliyor)

### Mezun İstihdam Verisi
- [x] `employment.py` model (EmploymentInfo, EmploymentListResponse)
- [x] `employment_service.py` (list, by_program, years - yıl bazlı)
- [x] `employment_data.json` (2026 data, sample CS programs)
- [x] API endpoints: `/employment/list`, `/employment/program/{code}`, `/employment/years`
- [x] Frontend API: `api.employmentList`, `api.employmentByProgram`, `api.employmentYears`
- [x] Frontend UI (istihdam bilgisi Compare.tsx'te gösteriliyor)

### Analytics Dashboard
- [x] `analytics.py` model (AnalyticsEvent, AnalyticsSummary)
- [x] `analytics_service.py` (log_event, summary, clear - JSON-based)
- [x] API endpoints: `/analytics/log`, `/analytics/summary`, `/analytics/clear`
- [x] Frontend API: `api.analyticsLog`, `api.analyticsSummary`, `api.analyticsClear`
- [x] Frontend admin paneli (Analytics.tsx)
- [x] 16 sayfaya page_view tracking eklendi

### TypeScript Migration (Başladı)
- [x] TypeScript + @types/react + @types/react-dom kuruldu
- [x] `tsconfig.json` ve `tsconfig.node.json` oluşturuldu
- [x] `constants.js` → `constants.ts` migrate edildi
- [x] `auth.js` → `auth.ts` migrate edildi
- [x] `api.js` → `api.ts` migrate edildi
- [x] `firestore-core.js` → `firestore-core.ts` migrate edildi
- [x] `firestore-study.js` → `firestore-study.ts` migrate edildi
- [x] `firestore-prefs.js` → `firestore-prefs.ts` migrate edildi
- [x] `firestore-plan.js` → `firestore-plan.ts` migrate edildi
- [x] `firestore-push.js` → `firestore-push.ts` migrate edildi
- [x] `firestore-user.js` → `firestore-user.ts` migrate edildi
- [x] `hooks.js` → `hooks.ts` migrate edildi
- [x] `index.js` → `index.ts` migrate edildi
- [x] Tüm 43 `.jsx` dosya → `.tsx` yeniden adlandırıldı
- [x] `index.html` → `main.tsx` referansı güncellendi
- [x] Proper type annotations (tsc --noEmit 0 hata, strict: false) - 15+ dosya typed

### Service Layer Migration (Önceki)
- [x] Tüm 16 sayfa + 3 component + 3 lib + 1 context migrate edildi
- [x] `firebase.js` tamamen kaldırıldı
- [x] Chunk splitting optimize edildi
- [x] Build: 631 URL prerender, 0 hata

## 🔄 Devam Eden / Sıradaki

### TypeScript Migration (Tamamlandı)
- [x] Proper type annotations ekleme (sayfa sayfa) — 43 dosya typed
- [x] `strict: true` yapma — 0 tsc error
- [x] Tip tanımları (interfaces, types) — types/index.ts + component interfaces

### ✅ Kariyer Data Sync her gün düşüyor (sahibi: opencode — kullanıcı onayıyla Claude Code düzeltti, 2026-11-03, commit bekliyor)
- [x] **Çözüm (uygulandı):** `kariyer_scraper.py`, `test_kariyer.py`, `test_kariyer_tarih_budama.py` son sağlam sürüme (`ecd4569^`) geri alındı. Yeniden yazım ayrıca koşu raporunu bozuyordu (`_gecmis_guncelle` `kariyer_kosu.json`'a `[]` yazıyor, workflow özet adımı `k['tarih']`'te çökecekti) ve `write_json_guarded`'ı zorunlu `label` olmadan çağırıyordu. Testteki 4 tarih-bombası (`_merge` `date.today()` kullanıyor) sabit tarih fixture'ıyla çözüldü; ruff 0.17 bulguları temizlendi. Sonuç: ruff temiz, 284 passed; kamuilan 403 simülasyonlu uçtan uca koşu exit 0. `kariyer_merge.py`/`jooble_scraper.py`/`careerjet_scraper.py`/`rg_scraper.py` artık scraper tarafından kullanılmıyor (yalnız `test_kariyer_tarih_budama` öncesinde import ediyordu) — silinip silinmeyeceği opencode'un kararı.
- **Açık kalan:** `kamuilan.sbb.gov.tr` GitHub runner IP'lerine 403 veriyor; CI'da bu kaynak 0 ilan getirecek (koşu yine yeşil, 🚨 alarm satırı basılır).
- **Dosya:** `backend/src/unisense/infrastructure/scrapers/kariyer_scraper.py:526` (`main()` içindeki kaynak çağrıları, ~520-553)
- **Sorun:** 2026-10-25'ten beri 9 koşunun 9'u `failure`. `kamuilan.sbb.gov.tr` GitHub runner'larına `403 Forbidden` dönüyor (lokalden 200 — runner IP'si engelleniyor). `_scrape_kamuilan` satır 87'deki `r.raise_for_status()` istisnayı yukarı fırlatıyor ve `main()` bunu yakalamadığı için kalan 9 kaynak hiç çalışmıyor, `kariyer` verisi 9 gündür güncellenmiyor.
- **Neden başladı:** `ecd4569` (2026-10-24, başlığı "test: fix embed_query import" ama scraper'ı yeniden yazıyor) eski `scrape_tumu()` içindeki kaynak başına `try/except` korumasını ("kısmi başarı normal (§5)") kaldırdı.
- **Önerilen çözüm:** `main()`'deki her `yeni.extend(_scrape_x(...))` çağrısını eski desendeki gibi `try/except Exception` ile sar; hatayı `print(f"  ⚠️ {ad} düştü: ...")` ile logla, kaynağı boş liste say. Hiçbir kaynak veri üretmezse exit 1 (eski guard) korunsun. Not: aynı yeniden yazımda `hatlar` (kamu/ozel) bölmesi ve kamuilan PDF `detayli` önbelleği de kayboldu — ayrıca değerlendir.

## 📋 Notlar
- Tüm özellikler ücretsiz olacak (premium kaldırıldı)
- Her özellik için build test + GitHub push yapıldı
- PWA + Error Boundary + Compare AI + Tercih Optimization + Unit Tests + Push Backend + Burs + İstihdam + Analytics + TypeScript Migration (başladı) tamamlandı
- Push notification: backend endpoint'ler + scheduler hazır, Firebase Admin SDK + service account key gerekli
- Burs/Ücret ve İstihdam: backend + API + frontend UI tamamlandı (Compare.tsx)
- Analytics: backend + API + frontend admin paneli + page view tracking tamamlandı
- TypeScript: tüm dosyalar .ts/.tsx, strict: false ile çalışıyor. Proper type annotations gradual olarak eklenebilir.