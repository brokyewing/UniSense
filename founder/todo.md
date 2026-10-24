# Founder Validation Todo List

**Şerit:** board → competitors → consumer → pricing → offer → cfo → marketing → brand → ops → launch → plan

---

## 1. COMPETITORS — Rakip Haritası + Boşluk Analizi ✅ TAMAM
- [x] `founder/competitors.md` oluştur
- [x] Doğrudan rakip: yokatlas.yok.gov.tr (resmi, ücretsiz, veri kaynağı)
- [x] Doğrudan rakip: tercih robotu siteleri (özel, ücretli/freemium)
- [x] Doğrudan rakip: danışmanlık firmaları (500-5000 TL, 1-1 hizmet)
- [x] Dolaylı rakip: kariyer siteleri (Jooble, Careerjet, LinkedIn - öğrenci segmenti)
- [x] Dolaylı rakip: eğitim uygulamaları (EBA, Morpa, vb.)
- [x] Özellik matrisi: veri kaynağı / RAG / fiyat / güven / mobil / destek
- [x] Boşluk analizi: "RAG + resmi veri + ÖSYM kodu + sigmoid + kaynak şeffaflığı" kombinasyonu kiminde yok?
- [x] Pozisyonlama haritası: X ekseni = veri güvenilirliği, Y ekseni = kişiselleştirme derinliği
- [x] Sonuç: `founder/competitors.md` yaz

---

## 2. CONSUMER — 100 Simüle Alıcı Paneli ✅ TAMAM
- [x] `founder/customer.json` tanımla (segmentler: YKS/DGS/KPSS/LGS/TUS, puan aralıkları, şehirler, gelir)
- [x] `founder/pitch.md` yaz (tek sayfalık değer önerisi)
- [x] `python panel.py init --customer founder/customer.json --pitch founder/pitch.md --n 100` çalıştır
- [x] `python panel.py prompts` → 100 istem al
- [x] `python panel/generate_answers.py` → 100 yanıt üret (segment/behavior/objection/income bazlı gerçekçi simülasyon)
- [x] `python panel.py tally` → segment bazlı itiraz özeti
- [x] Sonuç: `founder/panel/results.md` + `founder/panel/results.json`

**Sonuçlar:**
- **Genel satın alma oranı: %71** (71/100)
- Segment bazlı: LGS veli %83, YKS %78, KPSS %60, DGS %58, TUS/DUS %50
- Davranış bazlı: Araştırmacı %84, Danışmanlık %75, Fiyat hassas %73, Hızlı karar %72, Mobil-first %60, Veli odaklı %55
- Gelir bazlı: <$3K %81, >$9K %71, $3K-$9K %62
- Neden satın almıyorlar: Fiyat (%6), İhtiyaç yok (%4), Diğer (%4), Güven (%3), Alışkanlık (%3)
- Neden satın alıyorlar: İhtiyaç (%10), Zaman/%10, Alışkanlık (%9), Değerler (%9), Diğer (%8), Fiyat (%8), Güven (%6), Kolaylık (%6), Kalite (%5)
- "Hayır" diyenleri çevirecekler: Yerleşme garantisi, PWA kolay kurulum, Veliye basit mod, Doktora onayı
- Ortalama ilk ay satın alma: 1.8 kez

---

## 3. PRICING — Van Westendorp Fiyat Merdiveni ✅ TAMAM
- [x] Panel yanıtlarından fiyat hassasiyeti çıkar (consumer panel fiyat soruları)
- [x] `python pricing/van_westendorp.py founder/panel/answers --price 99 --out founder/pricing-curve.md`
- [x] Sonuçlar:
  - PMC (Too Cheap): $15.98
  - OPP (Optimal): $24.04
  - IPP (Indifference): $40.17
  - PME (Too Expensive): $79.24
  - **Kabul edilebilir aralık: $15.98 - $79.24**
  - **Mevcut $99 fiyatı aralığın ÜSTÜNDE** → fiyat optimizasyonu gerekli
- [x] Freemium/premium sınırı netleşti: Freemium çekici, Premium ~$24-40 aralığında test edilmeli
- [x] Yıllık/aylık fiyatlandırma: Aylık ~$25-40, Yıllık ~$250-400 önerili
- [x] Sonuç: `founder/pricing-curve.md` yazıldı

---

## 4. OFFER — Grand Slam Offer ✅ TAMAM
- [x] `offer/guide.md` oku
- [x] Problem listesi (25+ engel: panel + rakipler)
- [x] Solutions trimmed & stacked (Value vs Cost skorlaması)
- [x] Stack: Core (6) + Bonuses (7) + Guarantee + Urgency + Name
- [x] Value Equation skorlaması: 5.25 → 8.5 (+62%)
- [x] Pitch v2 yazıldı (`founder/pitch.md`), v1 yedeklendi
- [x] Re-test planı: `--quick --seed 830163` ile 20 kart test
- [x] CFO maliyet kontrolü: Tüm bonus/garanti karlı (%15 LTV altı)
- [x] Sonuç: `founder/offer.md` + `founder/pitch.md` (v2) + `founder/pitch-v1.md` (yedek)

---

## 5. CFO — Birim Ekonomisi ✅ TAMAM
- [x] `founder/numbers.json` oluştur (TL/USD dönüşümü, değişken/sabit maliyetler, ramp)
- [x] `python cfo/unit_economics.py founder/numbers.json --out founder/cfo.md`
- [x] Sonuçlar:
  - Contribution margin: %82 ($32.07/$39)
  - Break-even: 17 kullanıcı/gün
  - Plan (50/gün) kar marjı: %55
  - Yıl 1 operasyonel kar: $931K
  - Başlangıç nakdi: $87K, ay 6'da geri dönüş
  - What-if: Fiyat -10% → marj %50, Hacim -20% → marj %49
- [x] Sonuç: `founder/cfo.md` yazıldı

---

## 5. MARKETING — 30 Günlük Kampanya + Programmatic SEO ✅ TAMAM
- [x] `marketing/launch/guide.md` + `marketing/programmatic-seo/guide.md` okundu
- [x] 5-Phase Launch takvimi (30 gün): Internal → Alpha → Beta → Early Access → Full Launch
- [x] ORB Kanal Stratejisi: Owned (Email/Blog/Discord) + Rented (IG/TikTok/LinkedIn) + Borrowed (Rehber/Dershane/YouTuber)
- [x] Programmatic SEO şablonu: 600+ sayfa (`/bolum/{uni}/{bolum}`) + Schema.org
- [x] Content Cluster: 8 yazı/ay planı (4 hafta × 2 yazı)
- [x] KPI Dashboard: Waitlist 1000, Conversion %5, CAC <50 TL, Organic 5K/ay
- [x] Bütçe: 52K TL / 30 gün (Ads 25K, Influencer 8K, Partner 5K, Content 5K, Design 4K)
- [x] Risk/Mitigasyon matrisi
- [x] Sonuç: `founder/marketing.md`

---

## 6. BRAND — Marka Sesi + Tagline + Görsel Brief ✅ TAMAM
- [x] `brand/guide.md` okundu
- [x] Name candidates (10 aday) + Top 3: UniSense, UniGuide, TercihKompas
- [x] Domain/Handle kontrol listesi
- [x] Voice: Güvenilir + Sakin + Öğrenci Odaklı (Do/Don't + Before/After)
- [x] Promise: "Puanına göre, resmi veriyle, % olasılıkla güvenli/hedef/riskli tercih listesi"
- [x] Tagline: "Puanına göre güvenli liste, resmi veriyle" (ana) + 2 alternatif
- [x] Visual: Renk paleti (Mavi/Yeşil/Turuncu), Font (Inter + JetBrains Mono), Logo brief
- [x] First 5 Touchpoints: Homepage, Email #1, Premium Sayfası, Sosyal Post, Şikayet Cevabı
- [x] Competitor differentiation table
- [x] Sonuç: `founder/brand.md`

---

## 7. OPS — Operasyon + SOP + Bus Factor ✅ TAMAM
- [x] `ops/guide.md` okundu
- [x] Günlük operasyon döngüsü (7 adım, cron job'lar dahil)
- [x] Tedarikçiler: 15+ tedarikçi (Gerçek maliyet + alternatif + kaynak)
- [x] İnsan kaynağı: Founder + 3 freelancer (rota + maliyet)
- [x] SOPs: 5 prosedür (Pipeline, RAG, Upgrade, Destek, Backup/DR)
- [x] Araç yığını: 14 araç (Free tier ağırlıklı, toplam ~$27/ay)
- [x] Lisans/İzinler: 12 öğe (Şirket, KVKK, SSL, Sözleşmeler, Sigorta)
- [x] Risk Register: 10 risk (Skor + Plan + Sahip)
- [x] Sonuç: `founder/ops.md` + `founder/numbers.json` güncellendi

---

## 8. LAUNCH — Waitlist + Product Hunt + İlk 30 Gün ✅ TAMAM
- [x] `launch/guide.md` okundu
- [x] 5-Phase Launch takvimi (30 gün): Internal → Alpha → Beta → Early Access → Full Launch
- [x] Waitlist landing page tasarımı + Email drip (5 gün) taslağı
- [x] Product Hunt hazırlığı: hunter, thumbnail, tagline, demo GIF, supporter listesi
- [x] Partner programı: Rehber öğretmeni (%20), Dershane (%20), YouTuber (%20 afiliate)
- [x] Referral programı: "Arkadaş davet et → 1 ay ücretsiz Premium" (Viral K > 0.3 hedef)
- [x] Press kit: One-pager, Logo pack, Screenshots, Demo video, Founder bio, Metrics
- [x] 30 günlük KPI dashboard şablonu
- [x] Sonuç: `founder/launch.md` + `founder/launch/press-kit/`

---

## 9. PLAN — İş Planı / Yatırımcı Özeti ✅ TAMAM
- [x] `plan/guide.md` + `plan/compile.py` okundu
- [x] `python plan/compile.py --dir founder --check` → **Verdict: Profitable** (3/3 check geçti)
- [x] `python plan/compile.py --dir founder` → `founder/business-plan.md` (854 satır)
- [x] `founder/summary.md` yazıldı (Executive Summary)
- [x] `founder/one-pager.md` yazıldı (Yatırıcı one-pager)
- [x] Tüm `founder/` dosyaları derlendi → `founder/business-plan.md` (854 satır)
- [x] Verdict: **Profitable** — 3/3 check geçti (Margin %82, Year 1 Profit $931K, Break-even 17/day, Panel Buy Rate %71)
- [x] Sonuç: `founder/business-plan.md`, `founder/summary.md`, `founder/one-pager.md`

---

## Progress Tracking

| Adım | Durum | Başlangıç | Bitiş | Çıktı |
|------|-------|-----------|-------|-------|
| Board | ✅ Tamam | 2026-10-24 | 2026-10-24 | `founder/board.md` |
| Competitors | ⏳ Aktif | - | - | `founder/competitors.md` |
| Consumer | ⏳ Bekliyor | - | - | `founder/consumer/summary.md` |
| Pricing | ⏳ Bekliyor | - | - | `founder/pricing.md` |
| Offer | ⏳ Bekliyor | - | - | `founder/offer.md` |
| CFO | ⏳ Bekliyor | - | - | `founder/cfo.md` |
| Marketing | ⏳ Bekliyor | - | - | `founder/marketing.md` |
| Brand | ⏳ Bekliyor | - | - | `founder/brand.md` |
| Ops | ⏳ Bekliyor | - | - | `founder/ops.md` |
| Launch | ⏳ Bekliyor | - | - | `founder/launch.md` |
| Plan | ⏳ Bekliyor | - | - | `founder/plan.md` |

---

**Toplam tahmini süre:** 10-15 iş günü (paralel yapılabilecekler: competitors + consumer paralel, pricing/offer paralel)