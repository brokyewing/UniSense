# Marketing Plan — UniSense Pro (30 Günlük Lansman + Süreç)

**Tarih:** 2026-10-25  
**Versiyon:** v1.0  
**Strateji:** ORB Framework (Owned → Rented → Borrowed) + 5 Phase Launch

---

## 1. Mevcut Durum ve SLC Kontrolü

| Kriter | Durum | Not |
|--------|-------|-----|
| **Simple** | ✅ | Tek iş: "Puanına göre güvenli/hedef/riskli tercih listesi al" |
| **Lovable** | ⚠️ | RAG latency (cold start ~10s), PWA henüz yok, onboarding friksiyonlu |
| **Complete** | ⚠️ | Kariyer/Konular/Planım/LGS/TUS feature flag kapalı; PWA/PWA kurulum eksik |

**Karar:** Phase 1 (Internal) + Phase 2 (Alpha) paralel → PWA + onboarding iyileştirmesi **önce** lansman.

---

## 2. ORB Kanal Stratejisi

### Owned (Sahip Olduğumuz — Büyüyen Varlık)
| Kanal | Hedef | Aksiyon | KPI |
|-------|-------|---------|-----|
| **Email List** | Waitlist → Onboarding → Retention | Lead magnet: "Ücretsiz Tercih Raporu PDF" → 5 günlük email serisi | %25+ open rate, %5+ CTR |
| **Blog (SEO)** | Organik trafik | Programmatic SEO (600+ sayfa) + Content cluster | Ayda 10K+ organic session |
| **Discord Community** | Retention + Referral | "UniSense Öğrenci Topluluğu" — tercih paylaşımı, soru-cevap | 1000+ üye, günlük 50+ aktif |
| **Website** | Conversion | PWA, waitlist form, demo video, comparison pages | %3+ waitlist conversion |

### Rented (Kiralanan — Hız, Kontrolsüz)
| Platform | Hedef Kitle | İçerik Stratejisi | Sıklık |
|----------|-------------|-------------------|--------|
| **Instagram Reels** | Öğrenci (17-22) | "Tercih nasıl yapılır", "Bölüm tanıtımları", "Puan hesaplama" | 3x/hafta |
| **TikTok** | Öğrenci (16-20) | "Tercih robotu demo", "Puan hesaplama trick", "Bölüm günü" | 2x/hafta |
| **YouTube Shorts** | Veli + Öğrenci | "Tercih robotu nasıl çalışır", "Bölüm tanıtımları" | 1x/hafta |
| **LinkedIn** | Veli + Rehber öğretmen | "Tercih danışmanlığı neden önemli", "Veri odaklı karar" | 1x/hafta |
| **X (Twitter)** | EdTech/Tech topluluk | Lansman duyurusu, feature update, data insight | Günlük |

### Borrowed (Başkalarının Kitle — Hız + Güven)
| Fırsat | Hedef | Yaklaşım |
|--------|-------|----------|
| **Okul Rehber Öğretmenleri** | Veli/Öğrenci güven | "Rehber Öğretmeni Partner Programı" — ücretsiz premium erişim + komisyon |
| **Özel Dershaneler** | YKS/DGS segmenti | "Dershane Partner Programı" — toplu lisans + komisyon |
| **EdTech YouTuber'lar** (10K-100K abone) | Organik güven | Ürün demosu + affiliate link (%20 komisyon) |
| **Öğrenci Toplulukları** (Üni/Kulüp) | Genç kitle | Etkinlik sponsorluğu + waitlist QR |
| **Okul Dergileri/Gazeteleri** | Veli kitlesi | Basın bülteni + uzman görüşü (tercih stratejisi) |

---

## 3. 5-Phase Lansman Takvimi (30 Gün)

### Phase 1: Internal Launch (Gün 1-3) — "İç Test"
- [ ] 20 "arkadaş/aile" kullanıcısı recruting (WhatsApp/Email)
- [ ] Core flow test: Puan gir → Liste al → Kaydet → Paylaş
- [ ] RAG latency testi (cold/warm), PWA kurulum testi (Android/iOS)
- [ ] Bug bash: Critical path (puan gir → liste → kaydet → PDF)

### Phase 2: Alpha Launch (Gün 4-10) — "Waitlist Açılışı"
- [ ] Landing page: `unisense.com.tr/waitlist` — "Erken erişim + %70 indirim + yaşam boyu fiyat kilidi"
- [ ] Waitlist formu: Email + segment (YKS/DGS/KPSS/LGS/TUS) + veli/öğrenci
- [ ] Email capture → 5 günlük onboarding drip (Gün 1: Hoş geldin, Gün 2: Pusula demo, Gün 3: Tercih Robotu, Gün 4: PDF rapor, Gün 5: Açılış teklifi)
- [ ] 100 waitlist hedefi (Organik + 50 TL/gün Google Ads "YKS tercih" keyword)

### Phase 3: Beta Launch (Gün 11-20) — "Buzz Oluşturma"
- [ ] Teaser içerikleri: "Tercih Robotu 30 sn demo", "Pusula 3 soru", "PDF rapor örneği"
- [ ] 5 Rehber öğretmeni + 2 Dershane partner onboarding (ücretsiz premium erişim)
- [ ] 2 EdTech YouTuber (10K-50K abone) — ürün demosu + affiliate link
- [ ] 500 waitlist hedefi (Organik + Partner referral + 200 TL/gün Google Ads)
- [ ] Product Hunt listing hazırlığı (assets, hunter, tagline)

### Phase 4: Early Access Launch (Gün 21-27) — "Kontrollü Genişleme"
- [ ] Waitlist'ten 50 kullanıcıya "Early Access" daveti (ücretsiz 1 ay Premium)
- [ ] Kullanım verisi toplama: RAG latency, PWA kurulum oranı, feature adoption
- [ ] Product Hunt lansmanı (Gün 24-25) — Hunter, thumbnail, tagline, demo video
- [ ] Product Hunt günü: Tüm ekip engaged, her yoruma yanıt, trafiği waitlist'e yönlendir
- [ ] 1000 waitlist hedefi (PH trafiği + referral loop)

### Phase 5: Full Launch (Gün 28-30) — "Genel Açılış"
- [ ] Self-serve signup açılır (Stripe + Firebase)
- [ ] Genel duyuru: Email listesi, Blog yazısı, Social (tüm platformlar), Product Hunt
- [ ] Lansman paketi: Blog yazısı, Comparison pages, Demo video, Press kit
- [ ] Referral program aktif: "Arkadaş davet et → 1 ay ücretsiz Premium"
- [ ] Google Ads scale: 500 TL/gün → 2000 TL/gün (YKS sezonu yaklaştıkça)
- [ ] 30 günlük rapor: Waitlist → Activated → Paid conversion funnel

---

## 4. Programmatic SEO (600+ Sayfa — Kullanılabilir 30 günde)

### Şablon: `"X üniversitesi Y bölümü taban puanı 2024"`
- **URL yapısı:** `/bolum/{universite-slug}/{bolum-slug}`
- **İçerik:** Taban puan (3 yıl), sıralama, kontenjan, burs, fakülte, şehir, Kariyer sinyalleri (bölüm mezunu ilanlar)
- **Schema:** `Course`, `EducationalOrganization`, `FAQPage`
- **İç linkler:** Benzer bölümler, aynı üniversite diğer bölümleri, aynı şehirdeki üniversiteler

### Content Clusters (Blog — Haftalık 2 yazı)
| Hafta | Konu | Hedef Keyword | Format |
|-------|------|---------------|--------|
| 1 | "Tercih nasıl yapılır? Adım adım rehber" | tercih nasıl yapılır | Rehber (3000+ kelime) |
| 1 | "Bölüm seçimi: Puan mı İlgi mi?" | bölüm seçimi | Karşılaştırma |
| 2 | "Puan hesaplama: TYT/AYT/DGS/KPSS" | puan hesaplama | Hesaplayıcı + Rehber |
| 2 | "Güvenli/Hedef/Riskli tercih stratejisi" | güvenli hedef riskli tercih | Strateji |
| 3 | "Kariyer sinyalleri: Bölüm mezunu nereye?" | kariyer sinyalleri | Veri odaklı |
| 3 | "Veli rehberi: Çocuğuma nasıl yardımcı olayım?" | veli tercih rehberi | Veli odaklı |
| 4 | "2024 taban puanları: En çok talep edilen 10 bölüm" | 2024 taban puanları | Veri raporu |

**Hedef:** Ay 1'de 8 yazı → Ay 3'te 24 yazı → Ay 6'da 50+ yazı → Toplam 100+ içerik

---

## 5. KPI Dashboard (Haftalık Takip)

| Metrik | Hedef (30 Gün) | Ölçüm Araacı |
|--------|----------------|--------------|
| Waitlist kayıt | 1000 | Firestore + Mixpanel |
| Waitlist → Activated | %25 | Firebase Auth + Mixpanel |
| Waitlist → Paid (Premium) | %5 | Stripe + Mixpanel |
| Organic traffic (SEO) | 5000 session/ay | GA4 + Search Console |
| Referral signup | 100 | Firestore (referral code) |
| CAC (Blended) | < 50 TL | Mixpanel + Ads Manager |
| Activation rate (Waitlist → First login) | %40 | Mixpanel |
| Day 7 Retention | %30 | Mixpanel |
| NPS (Beta users) | > 40 | Typeform/Email |

---

## 6. Bütçe Dağılımı (30 Gün)

| Kalem | Bütçe (TL) | Not |
|-------|------------|-----|
| Google Ads (YKS/tercih keyword) | 15,000 | Günlük 500 TL → 15. gün 2000 TL |
| Meta Ads (IG/TikTok) | 10,000 | Test → Scale |
| YouTube Sponsor (2 micro-influencer) | 8,000 | 2x 10-50K abone |
| Partner Komisyon (Dershane/Rehber) | 5,000 | %20 revenue share |
| Content/SEO (Yazarlık + SEO araçları) | 5,000 | Ahrefs + Yazarlık |
| Tasarım/Video (Demo, Reels, Thumbnail) | 4,000 | Freelancer |
| **Toplam** | **52,000 TL** | ~$1,500 |

---

## 6. Riskler ve Mitigasyon

| Risk | Olasılık | Etki | Mitigasyon |
|------|----------|------|------------|
| Google Core Update (SEO trafiği düşüş) | Orta | Yüksek | Content cluster çeşitliliği, Brand traffic odaklı, Email listesi |
| Product Hunt flop | Düşük | Orta | Pre-launch hunter + supporter listesi (50+ kişi) hazır |
| RAG latency / hata (Kullanıcı kaybı) | Orta | Yüksek | Warmup + Cache + Fallback mesaj + Hata butonu |
| PWA kurulum zorluğu | Yüksek | Orta | QR + Video rehber + "Basit mod" toggle |
| Reklam maliyeti artışı (YKS sezonu) | Yüksek | Orta | Organic/Referral oranını %50+ tut, CAC cap koy |

---

## 7. Sonraki Adımlar (Bu Hafta)

1. [ ] **Landing page + Waitlist formu** deploy (Vercel + Firestore)
2. [ ] **Email drip (5 gün)** taslağı yaz + MailerSend/MailerLite entegrasyonu
3. [ ] **PWA manifest + Service Worker** + QR kod generator + Demo video
4. [ ] **Partner outreach** — 10 rehber öğretmeni + 3 dershane cold email
4. [ ] **Product Hunt assets** hazırla (Hunter, Thumbnail, Tagline, Demo GIF)
5. [ ] **Google Ads** kampanya kur (YKS/tercih keyword, negative keyword listesi)

---

## Sonraki Adım: Brand → Ops → Launch → Plan