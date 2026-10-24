# Launch Plan — UniSense Pro (30 Gün)

**Tarih:** 2026-10-25  
**Versiyon:** v1.0  
**Dayanak:** `founder/marketing.md`, `founder/offer.md`, `founder/brand.md`

---

## 1. Lansman Stratejisi Özeti

| Aşama | Gün | Odak | Hedef |
|-------|-----|------|-------|
| **Phase 1: Internal** | 1-3 | Core flow test, bug bash | 20 test kullanıcısı, 0 kritik bug |
| **Phase 2: Alpha** | 4-10 | Waitlist açılışı | 100 waitlist |
| **Phase 3: Beta** | 11-20 | Buzz + Partner | 500 waitlist, 5 partner |
| **Phase 4: Early Access** | 21-27 | Product Hunt + Early Access | 1000 waitlist, PH top 5 |
| **Phase 5: Full Launch** | 28-30 | Genel açılış | Self-serve aktif, 50 paid |

---

## 2. Phase 1: Internal Launch (Gün 1-3)

### Hedef
Core flow (Puan gir → Liste al → Kaydet → PDF → Paylaş) testi, kritik bug sıfırlama.

### Aksiyonlar
| Görev | Sorumlu | Süre | Kriter |
|-------|---------|------|--------|
| 20 test kullanıcısı recruting (WhatsApp/Email/Üniversite topluluklar) | Founder | Gün 1 | 20 kişi onay |
| Core flow test: Puan gir → Liste al → Kaydet → PDF → Paylaş | Founder + 20 testçi | Gün 1-2 | 0 kritik bug |
| RAG latency testi: Cold start <10s, Warm <3s | Founder | Gün 2 | p95 <3s (warm) |
| PWA kurulum testi: Android (Chrome) + iOS (Safari) + QR | Founder | Gün 2 | 100% başarı |
| Bug bash: Critical path (Puan gir → Liste → Kaydet → PDF → Paylaş) | Founder + Testçiler | Gün 3 | 0 Critical, <5 Major |

### Çıktı
- **Test raporu:** `founder/launch/internal-test-report.md`
- **Bilinen issue'lar:** GitHub Issues (Critical: 0, Major: <3, Minor: <10)
- **Go/No-Go kararı:** Phase 2'ye geçiş onayı

---

## 2. Phase 2: Alpha Launch — Waitlist Açılışı (Gün 4-10)

### Hedef
Waitlist 100 kayıt, email drip aktivasyonu.

### Landing Page: `unisense.com.tr/waitlist`
**Üst Kısım (Hero):**
- Başlık: "Puanına göre güvenli liste, resmi veriyle."
- Alt başlık: "YKS/DGS/KPSS/LGS/TUS — Sigmoid % olasılık + Yerleşme Garantisi + Kaynak linki"
- CTA: "Erken Erişim + %70 İndirim + Yaşam Boyu Fiyat Kilidi" → Email input + Segment dropdown
- Trust signals: "YÖK Atlas resmi veri", "Sigmoid % olasılık", "Kaynak linki her cevapta", "71% alıcı alıyor (panel)"

**Form Alanları:**
- Email (zorunlu)
- Segment: YKS / DGS / KPSS / LGS / TUS / Veli
- Rol: Öğrenci / Veli / Rehber
- Referral code (opsiyonel)

**Alt Kısım:**
- Özellikler: Tercih Robotu, Pusula, PDF Rapor, Yerleşme Garantisi, Kariyer
- Social proof: "Beta kullanıcılarının %71'i alıyor"
- FAQ: "Ücretsiz ne kapsar?", "Garanti nasıl çalışır?", "PWA nasıl kurulur?"

### Email Drip (5 Gün — MailerSend/MailerLite)

| Gün | Konu | İçerik Özeti | CTA |
|-----|------|--------------|-----|
| **Gün 1** | "Hoş geldin! 5 günde tercih uzmanı olacaksın." | Hoş geldin, ne bekler? Bugün: Pusula — 3 soru, bölüm önerisi | "Pusula'yı Dene (30 sn)" |
| **Gün 2** | "Puanını gir, güvenli listeyi al." | Tercih Robotu demo: Puan gir → % olasılık + güvenli/hedef/riskli | "Tercih Robotu'nu Dene" |
| **Gün 3** | "Her cevapta kaynak linki + hata butonu." | RAG şeffaflığı: Kaynak linki + ÖSYM kodu + Hata butonu | "Kaynak Şeffaflığını Gör" |
| **Gün 4** | "Yerleşme garantisi: Yerleşmezsen para iade." | Premium garantisi: Koşullar + %50 indirim + yaşam boyu kilit | "Erken Erişim %70 İndirim" |
| **Gün 5** | "Yarın açılıyor: İlk 1000'e %70 indirim." | Son hatırlatma: Açılış teklifi, QR kod, PWA kurulum videosu | "İlk 1000'e Gir (%70 İndirim)" |

### Trafik Kanalları (Gün 4-10)
| Kanal | Bütçe | Hedef | Not |
|-------|-------|-------|-----|
| **Organic/Referral** | 0 TL | 40 kayıt | Partner referral (rehber/dershane) |
| **Google Ads (YKS/tercih)** | 500 TL/gün | 40 kayıt | Negative keyword listesi kritik |
| **Partner Referral** | 0 TL | 20 kayıt | 10 rehber öğretmeni + 3 dershane |

**Hedef:** 100 waitlist (Gün 10 sonu)

---

## 3. Phase 3: Beta Launch (Gün 11-20)

### Hedef
500 waitlist, 5 partner, buzz oluşturma.

### Aksiyonlar
| Görev | Sorumlu | Gün | Kriter |
|-------|---------|-----|--------|
| Teaser içerikler: "Tercih Robotu 30 sn demo", "Pusula 3 soru", "PDF rapor örneği" | Marketing (Freelancer) | Gün 11-13 | 3 video + 3 Reel/Short |
| 5 Rehber öğretmeni + 2 Dershane partner onboarding (ücretsiz premium) | Founder | Gün 11-15 | 7 partner aktif |
| 2 EdTech YouTuber (10K-50K abone) — Ürün demosu + Affiliate link | Founder | Gün 12-16 | 2 video yayında |
| Product Hunt assets hazırlığı (Hunter, Thumbnail, Tagline, Demo GIF) | Founder + Designer | Gün 14-18 | Assets hazır |
| 500 waitlist hedefi (Organik + Partner referral + 200 TL/gün Ads) | Marketing | Gün 11-20 | 500 kayıt |

### Partner Programı
| Partner Tipi | Komisyon | Faydaları | Hedef |
|--------------|----------|-----------|-------|
| **Rehber Öğretmeni** | %20 revenue share (yaşam boyu) | Ücretsiz Premium + Öğrenci takip paneli | 10 öğretmen |
| **Dershane** | %20 revenue share + toplu lisans indirimi | Öğrenci takip paneli + toplu yönetim | 5 dershane |
| **EdTech YouTuber** | %20 afiliate (ilk yıl) | Ücretsiz Premium + Özel kod | 5 kanal (10K-100K abone) |

---

## 4. Phase 4: Early Access + Product Hunt (Gün 21-27)

### Hedef
Product Hunt top 5, 1000 waitlist, early access feedback.

### Product Hunt Lansmanı (Gün 24-25)

**Hazırlık (Gün 21-23):**
- [ ] Hunter bul (EdTech/SaaS kategorisinde aktif hunter)
- [ ] Thumbnail: 1270x760px — "UniSense Pro — Yerleşme Garantili Tercih Asistanı"
- [ ] Tagline: "Puanına göre % olasılıkla güvenli liste — resmi veri, kaynak linki, yerleşme garantisi"
- [ ] Demo GIF (15 sn): Puan gir → Liste al → PDF indir → PWA kur
- [ ] Hunter'a önceden bildir + "First comment" hazırla
- [ ] Supporter listesi: 50+ kişi (arkadaş, aile, test kullanıcıları, partner)

**Lansman Günü (Gün 24):**
- [ ] 09:00 PH listing live
- [ ] 09:00-23:00: Tüm ekip engaged (her yoruma <5 dk yanıt)
- [ ] 09:30: Founder "First comment" — hikaye + teknik detay + teşekkür
- [ ] 10:00: Twitter/LinkedIn/IG announcement + PH linki
- [ ] 12:00: Email listeye "Product Hunt'teyiz!" + özel %10 ek indirim kodu
- [ ] 15:00: Partner'lara "Share" isteği + affiliate link
- [ ] 18:00: Reddit r/EdTech / r/Turkey / r/SaaS cross-post
- [ ] 20:00: Gün sonu raporu: Upvote, Comment, Traffic, Signup

**Post-PH (Gün 25-27):**
- [ ] Tüm comment'lere yanıt + "Teşekkürler!" 
- [ ] PH trafiğini waitlist'e yönlendir (UTM parametreleri)
- [ ] Engaged kullanıcılara "Early Access" daveti (ücretsiz 1 ay Premium)
- [ ] Feedback formu gönder (Typeform: 5 soru, NPS)
- [ ] 1000 waitlist hedefi

---

## 5. Phase 5: Full Launch (Gün 28-30)

### Hedef
Self-serve signup aktif, ödeme almaya başlama, genel duyuru.

### Launch Day (Gün 28)
| Saat | Aksiyon | Kanal | Sorumlu |
|------|---------|-------|---------|
| 09:00 | Self-serve signup aç (Stripe + Firebase) | Web | Founder |
| 09:30 | Genel duyuru emaili (Waitlist + Email listesi) | Email | Founder |
| 10:00 | Blog yazısı yayını: "UniSense Pro — Yerleşme Garantili Tercih Asistanı" | Blog + SEO | Content |
| 10:30 | Social posts (LinkedIn, Twitter/X, Instagram, TikTok) | Social | Marketing |
| 11:00 | Product Hunt "Launch" comment + update | Product Hunt | Founder |
| 12:00 | Press kit dağıtımı (10+ tech/edtech blog) | Email | Founder |
| 14:00 | Referral program aktif: "Arkadaş davet et → 1 ay ücretsiz Premium" | Web + Email | Founder |
| 15:00 | Google Ads scale: 500→2000 TL/gün | Ads | Marketing |
| 16:00 | In-app announcement (mevcut kullanıcılar) | App | Founder |
| 18:00 | Gün sonu raporu: Signup, Paid, CAC, Activation | Dashboard | Founder |

### Post-Launch (Gün 29-30)
- [ ] Onboarding email sequence aktif (5 günlük drip)
- [ ] Referral program tracking dashboard
- [ ] Feedback toplama (Typeform: 5 soru, NPS)
- [ ] Bug bash: Kullanıcı raporları → Critical fix → Deploy
- [ ] 30 günlük rapor hazırlama: Funnel (Waitlist → Activated → Paid), CAC, LTV, Churn

---

## 5. Lansman Malzemeleri (Assets)

### Basın Seti (Press Kit) — `founder/launch/press-kit/`
| Dosya | Format | İçerik |
|-------|--------|--------|
| `one-pager.pdf` | PDF (1 sayfa) | Problem, Çözüm, Metrikler, Team, İletişim |
| `logo-pack.zip` | ZIP | Logo (SVG/PNG), Favicon, App Icon, Brand guidelines |
| `screenshots/` | PNG (1280x720) | Home, Tercih Robotu, Pusula, PDF Raporu, PWA, Mobil |
| `demo-video.mp4` | MP4 (60 sn) | Hero demo: Puan gir → Liste → PDF → PWA kur |
| `founder-bio.md` | MD | Founder hikayesi, LinkedIn, Twitter |
| `key-metrics.md` | MD | 71% buy rate, 55% margin, 17 break-even, 6 ay payback |

### Product Hunt Listing
| Alan | Değer |
|------|-------|
| **Name** | UniSense Pro |
| **Tagline** | Puanına göre % olasılıkla güvenli liste — resmi veri, kaynak linki, yerleşme garantisi |
| **Description** | 280 karakter: "Türkiye'nin ilk RAG+taban puan tercih asistanı. Puanını gir → Sigmoid % olasılıkla güvenli/hedef/riskli liste (ÖSYM kodlarıyla). Her cevapta YÖK Atlas linki + hata butonu. Yerleşme garantisi: yerleşmezsen para iade. PWA, offline, reklamsız." |
| **Topics** | Education, SaaS, Artificial Intelligence, Productivity, Turkey |
| **Website** | https://unisense.com.tr |
| **Twitter** | @unisense |
| **Maker** | Founder adı + LinkedIn |

---

## 6. Referral Programı (Viral Loop)

**Mekanik:** "Arkadaş davet et → Ikınıza da 1 ay ücretsiz Premium"

| Unsur | Detay |
|-------|-------|
| **Davet Eden** | Her davet = 1 ay ücretsiz Premium (maks 12 ay) |
| **Davet Edilen** | İlk ay %50 indirim + 1 ay ücretsiz Premium |
| **Tracking** | Unique referral code (P001-REF-XXXX) → Firestore attribution |
| **Paylaşım** | WhatsApp / Telegram / Email / Link kopyala |
| **Limit** | Kullanıcı başına max 12 ay ücretsiz (12 davet) |
| **Fraud Koruması** | Aynı IP/Device/Email tekrar sayılmaz, premium aktif olunca sayılır |

**KPI:** Viral coefficient (K) > 0.3 hedefi → Her 3 kullanıcılı 1 yenisi organic gelmeli.

---

## 7. 30 Günlük Rapor Şablonu (Gün 30)

| Metrik | Hedef | Gerçekleşen | Durum |
|--------|-------|-------------|-------|
| Waitlist Toplam | 1000 | | ⏳ |
| Waitlist → Activated | %25 (250) | | ⏳ |
| Waitlist → Paid (Premium) | %5 (50) | | ⏳ |
| CAC (Blended) | < 50 TL | | ⏳ |
| Organic Traffic (30g) | 5,000 session | | ⏳ |
| Referral Signups | 100 | | ⏳ |
| Activation Rate (W→A) | %40 | | ⏳ |
| Day 7 Retention | %30 | | ⏳ |
| NPS (Beta) | > 40 | | ⏳ |
| MRR (Ay sonu) | $500+ | | ⏳ |

---

## Çıktı
- `founder/launch.md` (bu dosya)
- Lansman asset'leri: `founder/launch/press-kit/`
- Product Hunt listing hazır
- Sonraki: `founder-plan` → İş planı / Yatırımcı özeti