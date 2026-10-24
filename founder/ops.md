# Operations Plan — UniSense Pro

**Tarih:** 2026-10-25  
**Versiyon:** v1.0  
**Dayanak:** `founder/idea.md`, `founder/offer.md`, `founder/numbers.json`, `founder/marketing.md`

---

## 1. Günlük Operasyon Döngüsü (Gün Başlangıcı → Gün Sonu)

UniSense dijital bir SaaS ürünüdür; fiziksel teslimat/yükleme yoktur. Operasyon "veri pipeline → API → Frontend → Kullanıcı" döngüsüdür.

| Zaman | Adım | Açıklama | Müşteri Görür mü? | Sorumlu |
|-------|------|----------|-------------------|---------|
| 00:00 | **Veri Pipeline (Günlük Cron)** | YÖK Atlas/ÖSYM/URAP/Jooble/Careerjet/ATS scrap → clean → embed → ChromaDB upsert | ❌ | Geliştirici (Cron) |
| 06:00 | **Sistem Sağlık Kontrolü** | API health check, ChromaDB count, Gemini quota, Render/ Vercel uptime | ❌ | Geliştirici (Monitoring alert) |
| 08:00 | **Kariyer Verisi Güncelleme** | Jooble/Careerjet/ATS günlük çekim → normalize → merge → `_merge` budama | ❌ | Cron Job |
| 09:00 | **Destek/İletişim Kontrol** | Email/Typeform/Discord destek talepleri kontrolü, SLA 4h | ✅ | Geliştirici (Part-time) |
| 10:00 | **İçerik/SEO** | Programmatic sayfa kontrolü (404/500), blog yazısı planlama | ❌ | Content (Freelancer) |
| 12:00 | **Analytics/Metrics** | WAU/MAU, RAG latency p95, conversion funnel, quota usage kontrol | ❌ | Geliştirici |
| 14:00 | **Kariyer/Partner Outreach** | Rehber öğretmeni/Dershane partner onboarding, affiliate link paylaşımı | ✅ | Founder |
| 16:00 | **Social/Content** | Instagram/TikTok/LinkedIn içerik planlama, scheduling | ✅ | Marketing (Freelancer) |
| 18:00 | **Monitoring/Alert Check** | Error rate, latency p99, quota usage, error budget burn rate | ❌ | Geliştirici (Sentry/UptimeRobot) |
| 22:00 | **Backup/Disaster Recovery** | ChromaDB snapshot, Firestore export, GitHub repo mirror | ❌ | Cron Job |

---

## 2. Tedarikçiler (Suppliers) — Gerçek Maliyetler ve Alternatifler

| Girdi | Birincil Tedarikçi | Maliyet (Aylık) | Alternatif | Not |
|-------|-------------------|----------------|------------|-----|
| **Gemini API (RAG)** | Google AI Studio | $0 (Free tier 1500 RPD) | Gemini Pro ($0.00025/1K) | Quota yeterli; Pro plan $0.00025/1K token |
| **Firebase (Auth+Firestore+Storage)** | Google Firebase | $0 (Spark Plan) | Blaze Plan (Pay-as-you-go) | Spark quota yeterli; Blaze $0.18/100K read |
| **Backend Hosting** | Render (Starter) | $7/ay | Railway ($5), Fly.io ($5) | Starter yeterli; scale için $25/ay Pro |
| **Frontend Hosting** | Vercel (Pro) | $20/ay | Netlify (Free), Cloudflare Pages | Pro plan paylaşımlı |
| **Kariyer API (Jooble)** | Jooble API | ~$50/ay (Tahmini) | Careerjet (Free, rate-limited) | Jooble key gerekli; Careerjet free ama rate-limited |
| **Kariyer API (Careerjet)** | Careerjet | $0 (Free, rate-limited) | Jooble | Rate limit: 100 req/gün |
| **ATS API (Lever/Greenhouse)** | Doğrudan API | $0 (Açık API) | — | Rate limit: 100 req/dk |
| **Payment Gateway** | İyzico / Stripe | %2.9 + 0.50 TL/işlem | PayTR, PayU | TR için İyzico uygun; Stripe global |
| **Email (Transactional)** | SendGrid | $15/ay (100K email) | Mailgun, MailerSend | 100K/ay yeterli |
| **SMS (Hatırlatıcı)** | Twilio | $0.0075/SMS (TR) | Netgsm, Turkcell | TR numarası için Netgsm uygun |
| **Monitoring (APM)** | Sentry (Developer) | $0 (Free) | Datadog ($31/host) | Free tier yeterli |
| **Uptime Monitoring** | UptimeRobot | $0 (Free 50 monitor) | Better Uptime | Free tier yeterli |
| **Error Tracking** | Sentry | $0 (Free) | LogRocket | Free tier yeterli |
| **Analytics** | Mixpanel (Free) | $0 (100K MTU) | PostHog (Self-hosted) | Free tier yeterli |
| **Domain/SSL** | Namecheap / Cloudflare | ~$15/yıl | Porkbun, GoDaddy | Cloudflare proxy + SSL ücretsiz |
| **Monitoring/Alerting** | Sentry + UptimeRobot | $0 | Datadog ($31/host) | Free tier yeterli |

> **Not:** Tüm maliyetler `founder/numbers.json` ile senkronize. Gerçek teklif alındığında CFO yeniden çalıştırılmalı.

---

## 3. İnsan Kaynağı (People) — Roller ve Rota

### Mevcut Takım (Gün 1)
| Rol | Kişi | Saat/Hafta | Maliyet (Aylık) | Not |
|-----|------|------------|-----------------|-----|
| **Founder / Full-Stack Dev** | Sahip (Siz) | 20-30 saat | 15,000 TL (0.5 FTE equivalent) | Core dev, product, ops, marketing |
| **Frontend/UX (Freelance)** | Upwork/Fiverr | 10-15 saat | 5,000 TL | PWA, QR, onboarding, UI polish |
| **Content/SEO (Freelance)** | Upwork/İşkur | 10 saat | 3,000 TL | Blog, programmatic SEO şablonları |
| **Content/SEO (Freelance)** | Upwork/İşkur | 10 saat | 3,000 TL | Blog, programmatic SEO şablonları |
| **Tasarımcı (Freelance)** | Upwork/99designs | 5 saat | 2,000 TL | Logo, UI kit, demo video |

**Toplam Aylık Personel Maliyeti:** ~23,000 TL (Founder hariç ~8,000 TL)

### Haftalık Rota (Planlanmış Hacim: 50/gün → ~1500/ay)

| Gün | Founder (Siz) | Frontend Freelancer | Content Freelancer | Tasarımcı |
|-----|---------------|---------------------|-------------------|-----------|
| Pazartesi | Sprint planning, bug triage, partner outreach | PWA/QR/Video dev | Blog yazısı (2/hafta) | UI kit, demo video |
| Salı | Partner outreach (rehber/dershane), metrics review | PWA/QR/Video dev | SEO şablon kontrol | UI kit, demo video |
| Çarşamba | Bug fix, RAG tuning, CI/CD | PR review, deploy | SEO şablon üretim | Logo varyasyonları |
| Perşembe | Partner onboarding, support tickets | PWA test, bug fix | Keyword research | Social media asset |
| Cuma | Sprint review, retro, next week plan | Weekend deploy prep | Content calendar plan | Asset export |
| Cumartesi | **Ops/Support** (4h) | — | — | — |
| Pazar | **Off** | — | — | — |

> **Not:** Founder "ops/support" cuma-cumartesi 4 saat ayırır. Diğer günler 4-6 saat core dev.

---

## 4. SOPs (Standart Operasyon Prosedürleri) — Tek Sayfa

### SOP-001: Günlük Veri Pipeline (00:00 Cron)
```
1. GitHub Actions / Render Cron tetikler: scrape_all.py
2. Her scraper sırasıyla: RG → Jooble → Careerjet → ATS → Kamuilan → AkademikTR → Savunma → TÜRKSAT
3. Her scraper: normalize → v2_kayit → _merge → write_json_guarded
4. Başarısız scraper: retry 3x (exponential backoff) → Slack alert
4. Başarılı: ChromaDB upsert → embed_texts_local → write_json_guarded (kariyer_ilanlar.json)
5. Son: _kosu_raporu + _gecmis_guncelle → kariyer_kosu.json
```
**SLA:** 06:00'a kadar bitmeli. Başarısızsa 07:00 Slack alert → Manuel yeniden başlatma.

### SOP-002: RAG Sorgu (API /ask)
```
1. Gelen istek: query + top_k + history + user_context
2. Cache check (_response_cache) → HIT: retrieval + return
3. Intent routing: KPSS/DGS/YKS/Trend/Profil → context build
4. Retrieval: _keyword_search (ChromaDB $contains) + vector search
5. Context build: Profil + Sınav + Recommendation + Trend + RAG
6. LLM Generate (Gemini Flash-Lite) → response + citations
7. Cache write (TTL 1h) → Answer JSON return
```
**SLA:** p95 < 3s (warm), <10s (cold). Hata: fallback mesaj + log.

### SOP-003: Premium Upgrade (Stripe Checkout)
```
1. Kullanıcı "Premium'a Geç" tıklar → Frontend Stripe Checkout Session oluştur
2. Stripe webhook: checkout.session.completed → Firestore user.premium=true + expires_at
3. Email gönder: "Premium aktif! PDF rapor, garantili liste, kariyer sinyalleri..."
4. Firestore: user.premium=true, premium_expires_at=now+1month/year
5. Feature flag: user.premium=true → UI'de premium feature'lar görünür
```
**Rollback:** Stripe refund → Firestore premium=false → Email bildirim.

### SOP-004: Destek Talebi İşleme (SLA 4 saat)
```
1. Gelen: Email / Typeform / Discord / GitHub Issue
2. Tag: "bug" | "feature" | "billing" | "data" | "ux"
3. Öncelik: P0 (kritik: ödeme, veri kaybı) → 1 saat | P1 (RAG hata) → 4 saat | P2 (UX/Feature) → 24 saat
4. Çözüm: Fix → Deploy → Kullanıcıya bildirim + "Çözüldü" tag
5. Kapanış: "Çözüldü" tag + Notion/GitHub issue kapatma
```
**Eskalasyon:** P0 → Founder anında | P1 → 4 saat içinde | P2 → Sprint'e al

### SOP-005: Haftalık Backup / DR Test (Cumartesi 02:00)
```
1. ChromaDB: `chromadb export` → GCS bucket (versioned)
2. Firestore: `gcloud firestore export gs://bucket/backup/$(date)`
3. GitHub: `git push --mirror backup-repo`
4. Restore test (Ayda 1): Yeni Render service → backup'tan restore → API health check
```
**RTO:** 2 saat | **RPO:** 24 saat

---

## 5. Araç Yığını (Tool Stack) — Minimal & Gerekli

| Kategori | Araç | Plan | Maliyet (Aylık) | Neden |
|----------|------|------|-----------------|-------|
| **Payments** | Stripe / İyzico | Pay-as-you-go | %2.9 + 0.50 TL | Global + TR yerel |
| **Auth/DB** | Firebase (Auth + Firestore) | Spark (Free) | $0 | Auth + Real-time + Offline |
| **Hosting (BE)** | Render | Starter ($7) | $7 | Docker + Auto-deploy + Cron |
| **Hosting (FE)** | Vercel | Pro ($20) | $20 | Edge + Preview + Analytics |
| **Vector DB** | ChromaDB (Local) | Self-hosted | $0 (Render disk) | Embedding lokal, API yok |
| **LLM** | Gemini Flash-Lite | Free Tier | $0 | 1500 RPD quota |
| **Monitoring** | Sentry + UptimeRobot | Free | $0 | Error tracking + Uptime |
| **Analytics** | Mixpanel | Free (100K MTU) | $0 | Event tracking |
| **Email** | SendGrid | Free (100K) | $0 | Transactional + Marketing |
| **SMS** | Twilio | Pay-as-you-go | ~$5 | Hatırlatıcı bildirimleri |
| **Version Control** | GitHub | Free (Private) | $0 | CI/CD + Issues |
| **CI/CD** | GitHub Actions | Free | $0 | Test + Deploy + Cron |
| **Design** | Figma | Free | $0 | UI Kit + Prototype |
| **Project Mgmt** | Notion / Linear | Free | $0 | Sprint + Docs |

**Toplam Aylık Araç Maliyeti:** ~$27 (₺900) — Çok düşük, free tier'lar ağırlıklı.

---

## 6. Lisans, İzinler, Sigorta (Türkiye — Istanbul)

| İzin/Belge | Gerekli mi? | Kurum | Süre | Maliyet | Durum |
|------------|-------------|-------|------|---------|-------|
| **Şirket Kurulumu (LTD/AS)** | Evet | Ticaret Sicili Müdürlüğü | 1-2 hafta | ~5,000 TL | **Yapılacak** |
| **Vergi Levhası** | Evet | Vergi Dairesi | Anında | Dahil | **Yapılacak** |
| **KVKK Kayıt (Veri Sorumlusu)** | Evet (Veri işliyor) | KVKK | 30 gün | ~1,000 TL | **Yapılacak** |
| **Mesafeli Sözleşme Yasası Uyumu** | Evet (E-ticaret) | Tüketici Hakem Heyeti | Sürekli | İç kaynak | **Uyulacak** |
| **Mesafeli Satış Sözleşmesi** | Evet (Abone modeli) | Tüketici Hakem Heyeti | Sürekli | İç kaynak | **Hazırlanacak** |
| **İade/İptal Hakkı Bildirimi** | Evet (14 gün) | Tüketici Hakem Heyeti | Sürekli | İç kaynak | **Hazırlanacak** |
| **KVKK Aydınlatma Metni** | Evet | KVKK | Sürekli | İç kaynak | **Hazırlanacak** |
| **Gizlilik Politikası** | Evet | KVKK | Sürekli | İç kaynak | **Hazırlanacak** |
| **Çerez Politikası** | Evet | KVKK | Sürekli | İç kaynak | **Hazırlanacak** |
| **SSL Sertifikası** | Evet | Cloudflare/Let's Encrypt | 90 gün (auto) | $0 | **Aktif (Cloudflare)** |
| **İşveren Sigortası (SGK)** | Evet (Çalışan varsa) | SGK | Sürekli | Maaş %20-25 | **Çalışan olunca** |
| **Meslek Mesuliyet Sigortası** | Önerilir | Özel Sigorta | Yıllık | ~2,000 TL | **Değerlendirilecek** |
| **Kurum Sigortası (Siber/Sigorta)** | Önerilir | Özel Sigorta | Yıllık | ~3,000 TL | **Değerlendirilecek** |

> **Not:** Hukuki danışman/avukat onayı şart. Yukarıdaki bilgiler rehber niteliğindedir.

---

## 7. Risk Register (En Olası 10 Risk)

| # | Risk | Olasılık | Etki | Skor | Plan (Mitigasyon) | Sahip |
|---|------|----------|------|------|-------------------|-------|
| 1 | **Gemini API quota tükenmesi / servis kapatma** | Orta | Çok Yüksek | 8 | Multi-key rotation, local embedding fallback, cache agresif | Founder |
| 2 | **RAG hallucination / yanlış taban puanı** | Orta | Çok Yüksek | 8 | Kaynak linki + ÖSYM kodu + hata butonu + cache + golden set test | Founder |
| 3 | **Google Core Update / SEO trafik düşüşü** | Orta | Yüksek | 6 | Programmatic SEO çeşitliliği + Brand traffic + Email listesi | Founder |
| 4 | **Bus Factor = 1 (Tek geliştirici)** | Yüksek | Çok Yüksek | 9 | Docs + Test %80+ + Runbook + Contractor pool (2. dev) | Founder |
| 5 | **RAG Latency / Cold Start (>10s)** | Orta | Yüksek | 6 | Warmup cron + Cache agresif + Fallback mesaj | Founder |
| 6 | **Google Ads maliyeti artışı (YKS sezonu)** | Yüksek | Orta | 6 | Organic/Referral %50+ hedef + CAC cap ($50) | Founder |
| 7 | **Firebase/Render/Vercel kesintisi** | Düşük | Çok Yüksek | 5 | Multi-region deploy planı + Status page + Runbook | Founder |
| 8 | **KVKK/Veri ihlali / Şikayet** | Düşük | Çok Yüksek | 5 | KVKK compliance + Veri şifreleme + 72h bildirim prosedürü | Founder |
| 9 | **Rekabet: Rakipler RAG ekler** | Orta | Yüksek | 6 | Moat: Golden set benchmark + Kaynak şeffaflığı + Garanti | Founder |
| 10 | **PWA kurulum zorluğu / Kullanıcı kaybı** | Yüksek | Orta | 7 | QR + Video rehber + "Basit mod" toggle + Onboarding email | Founder |

---

## Çıktı
- `founder/ops.md` (bu dosya)
- `founder/numbers.json` (güncellenmiş maliyetlerle)
- Sonraki: `founder-launch` → `founder-plan`