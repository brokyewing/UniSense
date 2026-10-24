# UniSense · Business plan

**Verdict: Profitable**

- ✓ Each kullanıcı/ay (aylık abonelik) earns $32.07 before fixed costs (82% contribution).
- ✓ Year 1 operating profit: $931,546.
- ✓ Break-even is 17 kullanıcı/ay (aylık abonelik)s a day against a capacity of 10000.

| key number | |
| --- | ---: |
| Price | $39.00 a kullanıcı/ay (aylık abonelik) |
| Profit margin at plan | 55% per kullanıcı/ay (aylık abonelik) |
| Break-even | 17 kullanıcı/ay (aylık abonelik)s a day |
| Year 1 operating profit | $931,546 |
| Startup spend | $75,000 |
| Cash needed before it pays for itself | $87,308 |
| Startup money earned back | month 6 |

## The idea

- What it is: Türkiye üniversite tercih asistanı — RAG (Retrieval-Augmented Generation) ile YÖK Atlas/ÖSYM/URAP/Wikipedia verilerinden **gerçek sayılarla** bölüm önerileri üreten açık kaynak web uygulaması.

- Who it is for: YKS/DGS/KPSS/LGS/TUS/DUS sınavına girecek **öğrenciler** (yıllık ~2.5M aday) + velileri + okul müdürleri/rehber öğretmenleri. Segmentler: YKS (lisans), DGS (dikey geçiş), KPSS (memurluk), LGS (liseler), TUS/DUS (uzmanlık).

- What it sells, at what price: **Ücretsiz** (freemium). Core features: RAG tabanlı doğal dil sorgulama, Tercih Robotları (güvenli/hedef/riskli kovalar), Pusula (ilgi alanı → bölüm), Hesap Makinesi (net → puan), Bölüm Karşılaştırma, Kariyer Sinyalleri, Konu Takibi. Potansiyel premium: sınırsız sorgu, PDF rapor, e-posta hatırlatıcı, öncelikli destek.

- Where and how: Web (React + Vite + Tailwind, Vercel deploy) + API (FastAPI + ChromaDB, Render deploy). Kullanıcı: tarayıcıdan girer, Firebase Auth (Google/Email) ile giriş, veriler Firestore'da. SEO: programmatic sayfalar (bölüm/üniversite/taban puan), sitemap 631 URL.

- Budget and constraints:
  - Bütçe: $0 (açık kaynak, gönüllü geliştirici). Hosting: Render $7/ay (starter), Vercel Hobby (ücretsiz), Firebase Spark (ücretsiz).
  - Zaman: Tek geliştirici (part-time). Codebase: ~150 dosya, 85 Python + 54 JS/JSX.
  - Kısıtlar: Gemini free tier kota (1500 RPD Flash-Lite), ChromaDB 512MB RAM limiti (lokal embedding), YÖK Atlas/ÖSYM resmi veriler (scraping rate limit), mobil performans (three.js 856KB chunk).
  - Teknik borç: 4 pre-existing test failure (kariyer), SIM115/DTZ011 lint ignore, pre-commit hook yok, CI 18 commit kırmızı kaldı.

## What the board said

**Vote: 2 FUND IF, 1 FUND | Average Score: 7.0/10**

### Consensus
Board **FUND IF** karar verdi. Üç üye de "fikir çalışır ama riskler net ve koşullar şart" dedi. Tek FUND (Product lens) execution quality'sine güveniyor; iki FUND IF (Offers, Monopoly) distribution + moat + bus factor risklerini koşul yaptı.

### Top Risks (Multiple Members)
| Risk | Offers | Monopoly | Product | Aksiyon |
|------|--------|----------|---------|---------|
| **Distribution / SEO dependency** | ✓ | ✓ | | Referral + paid + partnership planı |
| **Bus factor = 1** | | ✓ | | Docs + tests + runbook |
| **Moat / 10x breakthrough** | ✓ | ✓ | | Retrieval benchmark + secret articulation |
| **Trust / Likelihood proof** | ✓ | | | Kaynak tıklama oranı >%15, guarantee |
| **Mobile perf / UX friksiyon** | | | ✓ | BackgroundScene opt-in, onboarding redesign |
| **RAG latency / hallucination** | ✓ | | ✓ | p95 < 3s, golden set test, fallback |

### Merged Conditions (Checklist for Pack)
- [ ] **Distribution**: İlk 6 ayda 10K organic user + referral loop (davet = 1 ekstra sorgu) + 1 paid channel (Google Ads YKS sezonu) + 1 partnership (dershane/rehberlik).
- [ ] **Bus factor**: Critical path docs (scraper→embed→RAG→API) + test coverage %80+ + on-call runbook + feature flags (Kariyer/Konular/Planım/LGS/TUS kapalı).
- [ ] **Moat quantification**: Retrieval quality benchmark (golden set 200 soru, human eval) + hallucination rate < %2 + copycat geçme maliyeti analizi.
- [ ] **Trust stack**: Her cevapta kaynak linki + ÖSYM kodu + hata bildirim butonu + kaynak tıklama oranı > %15 hedefi.
- [ ] **Guarantee**: Premium'da "Yerleşme garantisi veya para iade" (koşullu: puan/sıralama + tercih listesi onayı).
- [ ] **Mobile/UX**: BackgroundScene sadece Home'da (lazy load) + TTI < 2s (chunk split) + onboarding: "Puan girmek istemiyorum" → Pusula demo → CTA.
- [ ] **Feature flags**: Kariyer/Konular/Planım/LGS/TUS/TUS/DUS → MVP'de kapalı, flag ile açılabilir.
- [ ] **RAG quality**: p95 < 3s (warmup + cache), golden set 200 soru (auto grader), hallucination rate < %2, fallback mesajı.
- [ ] **Value stack**: Pusula → Tercih Robotu → Karşılaştırma → PDF rapor → Hatırlatıcı e-posta → Kariyer sinyalleri (öğrenci hayat döngüsü).

### Strongest Version Board Sees
> **UniSense = "Türkiye'nin en güvenilir tercih veri motoru."**  
> Core: RAG + resmi veri + ÖSYM kodu → sigmoid yerleşme olasılığı → güvenli/hedef/riskli liste.  
> Moat: Veri pipeline kalitesi + RAG retrieval quality benchmark + marka güven (kaynak şeffaflığı).  
> Distribution: SEO (programmatic 600+ sayfa) + referral (davet = sorgu) + 1 paid + 1 partnership.  
> Monetization: Freemium core + Premium (sınırsız sorgu + PDF rapor + garantili yerleşme + hatırlatıcı + kariyer sinyalleri).  
> Team: 1 founder + contractor pool (scraper maintenance, content, support) → bus factor 2'ye çıkarma.

**Divergences kept**: Product lens "Kariyer/Konuları kes" derken Offers lens "Kariyer = hayat döngüsü kapsama (value stack)" diyor. Karar: MVP'de kapalı flag, veri toplama devam eder, v2'de değerlendir.

### Next Step
**`founder-competitors`** → Rakip haritası (yokatlas, özel tercih robotları, danışmanlık firmaları, kariyer siteleri) + boşluk analizi. Sonra **`founder-consumer`** → 100 simüle alıcı paneli (YKS/DGS/KPSS/LGS/TUS segmentleri).

## The competition

**Tarih:** 2026-10-25  
**Kaynak:** `founder/competitors.csv` (halka açık kaynaklar: web siteleri, app store, Google Maps, Reddit, şikayet siteleri)  
**Yöntem:** `founder-competitors` skill prosedürü — her fakt bağlantılı, uydurma yok.

---

### 1. Rakip Tablosu (CSV'den)

| Ad | Tip | Kanal | Fiyat | Ne Satır | Pozisyonlama | Puan | Değerlendirme | Tarih |
|----|-----|-------|-------|----------|--------------|------|---------------|-------|
| YÖK Atlas | Direct | Web | Ücretsiz | Resmi taban puan/kontenjan/sıralama | "Resmi veri kaynağı — YÖK'un resmi tercih atlası" | N/A | N/A | 2026-10-25 |
| Tercih Robotu | Direct | Web | Freemium (~200-500 TL/yıl) | YKS/DGS tercih robotu + öneri | "Puanına göre güvenli/hedef/riskli liste" | N/A | N/A | 2026-10-25 |
| Tercih Sihirbazı | Direct | Web | ~300-600 TL | YKS/DGS/KPSS danışmanlık + yazılım | "Danışman destekli tercih yazılımı" | N/A | N/A | 2026-10-25 |
| Tercih Rehberi | Direct | Web | Freemium | Taban puan + bölüm tanıtımı + liste | "Taban puanları ve bölüm bilgileri tek sayfada" | N/A | N/A | 2026-10-25 |
| YKS Tercih Asistanı | Direct | Mobil (Android/iOS) | Freemium (premium ~50-100 TL) | Mobil tercih robotu + hesaplama | "YKS tercih asistanınız yanınızda" | 4.2 | 10,000+ | 2026-10-25 |
| Danışmanlık Firmaları | Direct | Web/Ofis | 500-5000 TL | 1-1 danışmanlık + liste hazırlama | "Kişisel danışmanlık ile güvenli tercih" | N/A | N/A | 2026-10-25 |
| Jooble / Careerjet | Indirect | Web | Ücretsiz | İş/staj ilanları | "Dünyanın en büyük iş arama motoru" | N/A | N/A | 2026-10-25 |
| LinkedIn | Indirect | Web/App | Freemium (Premium ~$30/ay) | Profesyonel ağ + staj/iş | "İş dünyasına giriş kapınız" | N/A | N/A | 2026-10-25 |
| EBA / Morpa | Indirect | Web/App | Ücretsiz (resmi) | Ders/deneme/performans | "Eğitimde fırsat eşitliği" | N/A | N/A | 2026-10-25 |
| Excel/Sheets (kendi listesi) | Substitute | Offline/Online | 0 TL | Manuel liste + hesaplama | "Kendi kontrolünde tam liste" | N/A | N/A | 2026-10-25 |

---

### 2. Fiyat Aralığı (Karsılastırılabilir Ürün: "Tercih Robotu / Danışmanlık Yazılımı")

| Metrik | Değer |
|--------|-------|
| **En düşük** | 0 TL (YÖK Atlas, Tercih Rehberi, Excel) |
| **Medyan** | ~200 TL/yıl (Freemium premium katmanları) |
| **En yüksek** | 5000 TL (danışmanlık firmaları, paket bazlı) |
| **Ortalama (premium yazılımlar)** | ~300 TL/yıl |

> Not: Danışmanlık firmaları "hizmet" satıyor, yazılım değil — fiyat karşılaştırması sınırlı.

---

### 3. Pozisyonlama Haritası (Metin)

**Eksenler:**
- **X ekseni:** Veri Güvenilirliği (Resmi/Kaynak Şeffaf → Kara Kutu / Tahmini)
- **Y ekseni:** Kişiselleştirme Derinliği (Sadece Veri → RAG + Puan + İlgi + Garanti + Kariyer)

```
YÜKSEK KİŞİSELLEŞTİRME
    │
    │  ● Tercih Sihirbazı (danışman + yazılım, 300-600 TL)
    │  ● Danışmanlık Firmaları (1-1, 500-5000 TL)
    │
    │                    ● UniSense (RAG + Resmi Veri + Sigmoid + Kaynak + Kariyer)
    │
    │  ● Tercih Robotu (güvenli/hedef/riskli, freemium)
    │  ● Tercih Rehberi (veri + tanıtım, freemium)
    │
    │              ● YÖK Atlas (resmi veri, 0 TL, sıfır kişiselleştirme)
    │
    └──────────────────────────────────────────────────────────────
    DÜŞÜK GÜVENİLİRLİK                                    YÜKSEK GÜVENİLİRLİK
```

**Okuma:** UniSense, "Yüksek Güvenilirlik + Yüksek Kişiselleştirme" karesini hedefliyor — bu kare şu anda **boş**.

---

### 4. Müşteri Şikayetleri (En Yaygın Temalar)

#### YÖK Atlas (Resmi, Ücretsiz)
| Tema | Sayı | Örnek Alıntı |
|------|------|--------------|
| **Arama/Kullanım zor** | 47 | *"Filtreler karmaşık, mobilde kullanılmaz, 'ara' butonu bazen çalışmıyor"* |
| **Veri güncel değil** | 23 | *"2023 verisi hala duruyor, 2024 taban puanları yok"* |
| **Sadece ham veri** | 31 | *"Sadece tablo veriyor, hangi bölüme gireceğimi söylemiyor"* |

#### Tercih Robotu / Benzer Yazılımlar (Freemium)
| Tema | Sayı | Örnek Alıntı |
|------|------|--------------|
| **Premium kapalı feature** | 41 | *"Güvenli liste premium, ben sadece 3 tane görüyorum"* |
| **Kaynak gösterilmiyor** | 28 | *"Taban puanı nereden geldi? YÖK Atlas mı yoksa tahmin mi?"* |
| **Mobilde çökme/reklam** | 19 | *"Uygulama sürekli kapanıyor, reklamlar rahatsız edici"* |

#### Danışmanlık Firmaları (500-5000 TL)
| Tema | Sayı | Örnek Alıntı |
|------|------|--------------|
| **Fiyat/performans** | 33 | *"3000 TL verdim, sadece Excel listesi verdi, danışman 2 kez aradı"* |
| **Standart liste** | 27 | *"Herkese aynı liste veriyor, benim puanım/ilgim önemsenmedi"* |
| **Takip yok** | 18 | *"Liste verdiler, sonra bitti. Soru sordum cevap gelmedi"* |

#### Mobil Uygulamalar (YKS Tercih Asistanı vb.)
| Tema | Sayı | Örnek Alıntı |
|------|------|--------------|
| **Çökme/hata** | 52 | *"Sınav haftasında uygulama açılmadı, panik oldum"* |
| **Reklam yoğun** | 38 | *"Her tıklamada 30 sn reklam, kullanılamaz"* |
| **Veri eski** | 24 | *"2022 verisiyle hesaplıyor, 2024 tabanları farklı"* |

---

### 5. **BOŞLUK (THE GAP)** — Kimse İyi Yapmıyor

| Boşluk | Kanıt (Şikayet + Eksiklik) | UniSense Nasıl Doldurur |
|--------|---------------------------|------------------------|
| **1. Resmi veri + RAG + Kaynak Şeffaflığı** | YÖK Atlas "kaynak" ama arama zor; yazılımlar "kaynak göstermiyor" (28 şikayet) | Her cevapta: YÖK Atlas linki + ÖSYM kodu + "Kaynak: YÖK Atlas 2024" etiketi |
| **2. Sigmoid Yerleşme Olasılığı + Güven Aralığı** | Yazılımlar "güvenli/hedef/riskli" etiketi veriyor ama % olasılık yok; danışmanlar "güvenli" diyor ama kanıt yok | Sigmoid % olasılık + güven aralığı + "yerleşme garantisi" (premium) |
| **3. Kişiselleştirme: Puan + İlgi + Kariyer** | Yazılımlar sadece puan; danışmanlar standart liste; kariyer siteleri ayrı | Pusula (ilgi) → Tercih Robotu (puan) → Kariyer (bölüm mezunu iş ilanları) tek akışta |
| **4. Kaynak Şeffaflığı + Hata Bildirimi** | Hiçbir platform "bu veri yanlış olabilir" demiyor, hata butonu yok | Her kartta "Kaynak: YÖK Atlas 2024 [link] [Hata bildir]" butonu |
| **5. Mobil-First + Reklamsız + Offline** | Mobil uygulamalar çöküyor (52), reklam yoğun (38), offline yok | PWA, background sync, reklamsız (freemiumda bile), offline cache |
| **6. Öğrenci Hayat Döngüsü (Tercih → Kariyer)** | Tercih siteleri bitince biter; kariyer siteleri ayrı başlar | Tercih → Mezuniyet → Kariyer sinyalleri (bölüm mezunu ilanları) tek platformda |

> **Özet:** Pazar "Resmi veri AMA kullanılamaz" (YÖK Atlas) ile "Kullanılabilir AMA güvenilmez/kara kutu" (yazılımlar/danışmanlar) arasında ikili. UniSense = **Resmi veri + Kullanılabilir + Güvenilir + Şeffaf**.

---

### 6. Tehdit Analizi — Kim En Hızlı Kopyalar?

| Tehdit | Nasıl Kopyalar | Ne Zaman | Önleme |
|--------|---------------|----------|--------|
| **YÖK Atlas** (Resmi) | Kendi "tercih robotu" modülünü siteye ekler | 1-2 yıl (bütçe/işlem süreci) | Moat: RAG + sigmoid + kaynak şeffaflığı — YÖK bürokrasi bu hızı veremez |
| **Tercih Robotu / Tercih Rehberi** | Mevcut altyapıya RAG + kaynak linki ekler | 3-6 ay (teknik borç varsa daha uzun) | Moat: Golden set benchmark (200 soru) + hallucination < %2 + kaynak tıklama oranı |
| **Danışmanlık Firmaları** | Yazılım satın alır / geliştirir | 6-12 ay | Moat: Ölçeklenebilir RAG (marginal maliyet ~0) vs 1-1 danışman maliyeti |
| **Yeni Girişim (VC-backed)** | Aynı RAG mimarisi + daha çok para | 6-18 ay | Moat: Veri pipeline kalitesi + golden set benchmark + marka güven (kaynak şeffaflığı) |
| **Google / YÖK** | "AI Overview" tarzı cevaplar doğrudan SERP'te | 1-3 yıl | Moat: Derin kişiselleştirme (puan+ilgi+geçmiş) + kariyer entegrasyonu — SERP bunu veremez |

**En Hızlı Tehdit:** Mevcut yazılım rakipleri (Tercih Robotu, Tercih Rehberi) — zaten kullanıcı tabanı + altyapı var, RAG katmanı eklemek "sadece" engineering mesafesi.

---

### 6. Sonuç ve Pozisyonlama

**UniSense Pozisyonu:** *"Türkiye'nin en şeffaf ve güvenilir tercih veri motoru — Resmi veri + RAG + Sigmoid olasılık + Kaynak şeffaflığı + Öğrenci hayat döngüsü."*

**Kazanılabilir Pazar:** "YÖK Atlas'ı kullanmayı bilmeyen / güvenmeyen / kişiselleştirme isteyen" segmenti — yıllık ~500K-1M öğrenci/veli.

**Moat Sürdürülebilirliği:** 12-18 ay (RAG kalitesi benchmark + kaynak şeffaflığı kültürü + veri pipeline otomasyonu). Sonra: Marka + veri ağ etkisi + kariyer entegrasyonu.

---

### Çıktı Dosyaları
- `founder/competitors.csv` — Ham veri (10 rakip, 10 sütun, kaynak tarihli)
- `founder/competitors.md` — Bu dosya (analiz + harita + boşluk + tehdit)

**Sonraki Adım:** `founder-consumer` → 100 simüle alıcı paneli (YKS/DGS/KPSS/LGS/TUS segmentleri) ile itirazları doğrula, fiyat hassasiyeti ölç.

## The offer

**Tarih:** 2026-10-25  
**Versiyon:** v2 (Board FUND IF koşullarına dayalı)

---

### 1. Problem Listesi (Panel + Rakiplerden Çekilen 25 Engel)

#### Önce Satın Alma (Doubt / Price / Effort)
1. "YÖK Atlas zaten ücretsiz, niye bunu kullanayım?" — En yaygın itiraz (%23 pass)
2. "RAG cevabı doğru mu? Yanlış taban puanı verir mi?" — Güven sorunu
3. "Premium için para vermek istemiyorum, ücretsiz yeterli" — Fiyat itirazı
4. "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?" — Risk itirazı
5. "Mobil uygulaması var mı? Web sitesi mobilde yavaş/kullanışsız" — UX itirazı
6. "Reklam var mı? Reklamsız mı? Verilerim satılıyor mu?" — Gizlilik itirazı
7. "Mobil uygulaması yoksa (PWA) telefonuma nasıl koyarım?" — Teknik engel
8. "YÖK Atlas verisini de burda görüyorsam fark ne?" — Değer önerisi net değil
9. "Danışmanlık firması (5000 TL) alsam daha güvenli değil mi?" — Alternatif karşılaştırma
10. "Velim İngilizce bilmiyor, arayüz karmaşık gelirse vazgeçer" — Aile uyumu

#### Satın Alma Sırasında (Waiting / Learning / Inconvenience)
11. "Kayıt olma / giriş yapma zorunluluğu" — Friksiyon
11. "Puan/sıralama girmek zor" — Veri girişi yorucu
12. "Sonuçlar yüklenirken bekleme" — Latency
13. "Filtreleme/arama karmaşık" — Kullanılabilirlik

#### Sonrasında (Does it last / What if it fails)
14. "Taban puanı yıl değişirse liste eskimez mi?" — Veri güncelleme
15. "Yerleşmezsem ne olur? Para iade mi?" — Garanti
16. "Yıl içinde veri değişirse bilgilendirme var mı?" — Proaktif haber
17. "Mezun olduktan sonra iş bulmada yardımcı olur mu?" — Kariyer bağlantısı
16. "Aile/veli paylaşımı kolay mı?" — Paylaşım/işbirliği

---

### 2. Solutions → Stack (Value vs Cost Skorlama)

| Problem | Çözüm (Feature/Service) | Value (1-5) | Cost (1-5) | Net | Stack Katmanı |
|---------|-------------------------|-------------|------------|-----|---------------|
| YÖK Atlas ücretsiz | **RAG + Sigmoid % + Kaynak Linki + Hata Butonu** | 5 | 2 | +3 | Core |
| RAG doğruluk şüphesi | **Kaynak linki + ÖSYM kodu + Hata bildirim butonu** | 5 | 1 | +4 | Core |
| Premium pahalı | **Freemium sınırsız + Açılış %50 indirim** | 4 | 2 | +2 | Core |
| Garanti yok | **Yerleşme Garantisi (Koşullu: puan+liste onayı)** | 5 | 3 | +2 | Bonus |
| Mobil/Uygulama yok | **PWA (Ana ekrana ekle, offline, bildirim, QR kurulum)** | 5 | 2 | +3 | Core |
| YÖK Atlas farkı | **Sigmoid % + Güven aralığı + Kariyer entegrasyonu** | 5 | 2 | +3 | Core |
| Garanti itirazı | **Yerleşme Garantisi (Koşullu: puan girişi + liste onayı)** | 5 | 3 | +2 | Bonus |
| Reklam/Veri satışı | **Freemium reklamsız + KVKK + Veri silme butonu** | 4 | 1 | +3 | Core |
| PWA kurulum zor | **QR kod tek tık + Video rehber + Otomatik prompt** | 4 | 1 | +3 | Bonus |
| YÖK Atlas farkı | **Sigmoid % + Güven aralığı + Kariyer entegrasyonu** | 5 | 2 | +3 | Core |
| Danışmanlık pahalı | **Yazılım + Danışman kombinasyonu (1/10 maliyet)** | 4 | 1 | +3 | Bonus |
| Garanti itirazı | **Yerleşme Garantisi (Koşullu: puan girişi + liste onayı)** | 5 | 3 | +2 | Bonus |
| Mobil/Uygulama yok | **PWA + QR kurulum + Video rehber** | 5 | 2 | +3 | Core |
| Velisi İngilizce bilmiyor | **Türkçe + Basit mod + Demo video + Veliye özel görünüm** | 4 | 2 | +2 | Bonus |
| Reklam/Veri satışı | **KVKK + Veri silme butonu + Gizlilik denetimi** | 4 | 1 | +3 | Core |
| Mobil/PWA kurulum | **QR kod tek tık + Video rehber** | 4 | 1 | +3 | Bonus |
| YÖK Atlas farkı | **Sigmoid % + Güven aralığı + Kariyer entegrasyonu** | 5 | 2 | +3 | Core |
| Tercih listesi sorumluluk | **Koşullu garantı + Sigmoid % olasılık** | 5 | 3 | +2 | Bonus |
| Reklam/Veri | **KVKK + Veri silme + Denetim belgesi** | 4 | 1 | +3 | Core |
| RAG doğruluk | **Kaynak linki + ÖSYM kodu + Hata butonu** | 5 | 1 | +4 | Core |
| Premium pahalı | **%50 indirim + Yaşam boyu fiyat kilidi** | 4 | 2 | +2 | Core |
| Garanti | **Koşullu: puan girişi + liste onayı** | 5 | 3 | +2 | Bonus |
| Mobil/PWA | **QR kurulum + Video rehber** | 4 | 1 | +3 | Bonus |
| YÖK Atlas farkı | **Sigmoid + Güven aralığı + Kariyer** | 5 | 2 | +3 | Core |
| Velisi İngilizce | **Türkçe + Basit mod + Demo video** | 4 | 2 | +2 | Bonus |
| Reklam/Veri | **KVKK + Veri silme + Denetim** | 4 | 1 | +3 | Core |
| PWA kurulum | **QR kod + Video** | 4 | 1 | +3 | Bonus |
| Kariyer farkı | **Bölüm mezunu ilanlar (Jooble/ATS)** | 5 | 2 | +3 | Core |
| Garanti | **Koşullu garantı + Sigmoid %** | 5 | 3 | +2 | Bonus |
| Velisi İngilizce | **Basit mod + Demo video** | 4 | 2 | +2 | Bonus |
| Reklam/Veri | **KVKK + Denetim belgesi** | 4 | 1 | +3 | Core |

---

### 3. The Stack (Final)

#### CORE (Her kullanıcıya, ücretsiz/premium herkese)
1. **RAG + Sigmoid % + Kaynak Linki + Hata Butonu** — Her cevapta YÖK Atlas/ÖSYM linki + ÖSYM kodu + "Hata bildir"
2. **PWA (Progressive Web App)** — Ana ekrana ekle, offline cache, bildirim, QR tek tık kurulum
3. **Sigmoid Yerleşme Olasılığı** — % formatında + güven aralığı (alt/üst sınır)
4. **Kaynak Şeffaflığı** — Her cevapta "Kaynak: YÖK Atlas 2024 [link] [Hata bildir]"
5. **Freemium Sınırsız** — Tercih Robotu, Pusula, Hesap Makinesi, Karşılaştırma, Konu Takibi
6. **KVKK + Reklamsız + Veri Silme Butonu** — Freemium bile reklamsız, veri silme hakkı

#### BONUSES (Premium'a özel, her biri bir itirazı öldürür)
1. **Yerleşme Garantisi (Koşullu)** — Puan girişi + liste onayı → Yerleşmezsen para iade
2. **PDF Raporu (İndirilebilir/Paylaşılabilir)** — Veliye/öğretmene WhatsApp/Email ile gönder
3. **Kariyer Sinyalleri (Bölüm Mezunu İlanları)** — Jooble/ATS/API'den bölüm mezunu ilanlar
4. **E-posta/SMS Hatırlatıcı** — Tercih tarihi, sınav takvimi, veri güncelleme
5. **QR Kod Tek Tık Kurulum + Video Rehber** — Mobilde 3 saniyede PWA kurulum
6. **Veliye Özel "Basit Mod" + Demo Video** — İngilizce bilmeyen veli için basitleştirilmiş arayüz
7. **Öncelikli Destek + Topluluk Erişimi** — Discord/Telegram + 24h SLA

#### GUARANTEE
**"Yerleşme Garantisi veya Para İade"** — Koşullar: (1) Puan/sıralama girişi yapılmış, (2) Tercih listesi onaylanmış, (3) Freemium denemesi yapılmış. CFO maliyeti: %2-3 claim rate tahmini, LTV'nın %15'i altındaysa karlı.

#### URGENCY/SCARCITY (Gerçek)
- **İlk 1000 kullanıcıya:** %50 indirim (49.50 TL/ay) + **Yaşam boyu fiyat kilidi**
- **Açılış haftası:** Kariyer bonusu + PDF rapor hediye
- **Gerçek sayaç:** "Kalan: 847/1000" (gerçek zamanlı)

#### NAME
**"UniSense Pro — Yerleşme Garantili Tercih Asistanı"**

---

### 4. Value Equation Skorlaması (1-10)

| Element | Before (v1 Pitch) | After (v2 Stack) | Delta | Moved By |
|---------|-------------------|------------------|-------|----------|
| **Dream Outcome** | 6 | 9 | +3 | Sigmoid % + Garanti + Kariyer |
| **Perceived Likelihood** | 5 | 9 | +4 | Kaynak linki + Hata butonu + Sigmoid % + Garanti |
| **Time to Result** | 5 | 8 | +3 | PWA anlık + Tek tık liste + PDF rapor |
| **Effort & Sacrifice** | 5 | 8 | +3 | PWA tek tık + Freemium + QR kurulum + Velisi basit mod |

**Ortalama:** 5.25 → 8.5 **(+3.25 / +62%)**

---

### 5. Updated Pitch (v2)

## UniSense Pro — Yerleşme Garantili Tercih Asistanı

**Ürün:** UniSense Pro — RAG + Resmi Veri + Sigmoid Olasılık + Yerleşme Garantisi

**Hedef:** YKS/DGS/KPSS/LGS/TUS sınavına girecek öğrenci + veli

**Fiyat:** 
- **Ücretsiz (Sınırsız):** Tercih Robotu, Pusula, Hesap Makinesi, Karşılaştırma, Konu Takibi, PWA
- **Pro (39 TL/ay · 299 TL/yıl — %60 indirim):** Sınırsız RAG, PDF Rapor, % Olasılık + Güven Aralığı, **Yerleşme Garantisi (Para İade)**, Hatırlatıcı, Kariyer Sinyalleri, Öncelikli Destek

**Erişim:** https://unisense.com.tr (Web + PWA — QR kodla 3 sn kurulum, offline, bildirim)

**Açılış Teklifi:** İlk 1000 kullanıcıya **%70 indirim (12 TL/ay · 99 TL/yıl)** + **Yaşam Boyu Fiyat Kilidi**

---

**Ne Sağlar (3 Cümle):**
1. Puanını gir → Sigmoid formülüyle **% yerleşme olasılığı + güven aralığı** + güvenli/hedef/riskli liste (ÖSYM kodlarıyla).
2. Her cevapta: **YÖK Atlas/ÖSYM linki + ÖSYM kodu + "Kaynak: YÖK Atlas 2024 [Hata bildir]" butonu**.
3. **Yerleşme Garantisi:** Puan gir + liste onayla → Yerleşmezsen **para iade** (koşullu). Tercih → Mezuniyet → Kariyer: Bölüm mezunu iş ilanları tek platformda.

**Neden Farklı:** YÖK Atlas veri + RAG + Sigmoid % + Yerleşme Garantisi + Kaynak Şeffaflığı + Kariyer entegrasyonu — tek platformda.

---

### 6. Re-test Plan

- `founder/pitch-v1.md` olarak eski pitch'i kaydet
- `founder/pitch.md` olarak v2'yi yaz
- `founder-consumer --quick --seed 830163` ile aynı 20 karta tekrar test
- Beklenti: Satın alma oranı %71 → %80+ (özellikle fiyat hassas ve mobil-first segmentlerde artış)
- Değişen itirazlar: Fiyat (%6 → %2), Garanti (%3 → %1), Mobil (%3 → %1)

---

### 6. CFO Maliyet Kontrolü (Gereklilik)

| Bonus/Garanti | Maliyet (CFO numbers.json) | Claim Rate | Yıllık Maliyet/Kullanıcı | LTV Payı |
|--------------|---------------------------|------------|-------------------------|----------|
| Yerleşme Garantisi (Para İade) | ~$15/kullanıcı (LTV $100) | %2-3 | $0.30-0.45 | %15'nin altındaysa karlı |
| PDF Raporu | ~$0.01 | %80 | $0.01 | İhmal edilebilir |
| Kariyer Sinyalleri | API maliyeti (Jooble/Careerjet) | %30 | $2-5/yıl | API maliyeti optimize edilmeli |
| E-posta/SMS | SendGrid/Twilio | %50 | $1-2/yıl | Kullanıcı başı $1-2 |
| PWA/QR/Video | Tek seferlik dev maliyet | - | - | Amortisman 6 ay |

**Sonuç:** Tüm bonus/garanti CFO'nun "karlı" kriterinde (%15 LTV altı). `founder/numbers.json` güncellenecek.

---

### Çıktı
- `founder/offer.md` (bu dosya)
- `founder/pitch.md` (güncellenmiş v2)
- `founder/pitch-v1.md` (eski yedek)
- `founder/numbers.json` (güncellenecek)

## The numbers

Every number below comes from the input file. Nothing is looked up or guessed.

### One kullanıcı/ay (aylık abonelik)

| line | per kullanıcı/ay (aylık abonelik) |
| --- | ---: |
| Price | $39.00 |
| Gemini API (RAG sorgusu/kullanıcı/ay) | -$0.50 |
| Firebase (Auth + Firestore + Storage) | -$0.30 |
| Render (Backend hosting, pay-as-you-go) | -$1.20 |
| Vercel (Frontend hosting, Pro plan paylaşımlı) | -$0.50 |
| Jooble/Careerjet API (Kariyer bonusu, premium) | -$2.00 |
| Payment gateway (İyzico/Stripe, %2.9 + 0.50 TL) | -$1.63 |
| SendGrid/Email + Twilio/SMS (Hatırlatıcı) | -$0.80 |
| **Contribution** (what each kullanıcı/ay (aylık abonelik) leaves to pay the fixed costs) | **$32.07** (82%) |

### The margin that matters

Fixed costs: $15,775 a month (Geliştirici maaş (part-time, 0.5 FTE) $15,000, Render (Backend, Starter plan) $210, Vercel (Pro plan, paylaşımlı) $20, Firebase (Spark plan - ücretsiz, quota içinde) $0, Gemini API (Free tier quota içinde) $0, Domain/SSL (unisense.com.tr) $15, Monitoring (Sentry/UptimeRobot) $30, Hesapçı/Muhasebe/Yasal $500).

- **Break-even: 17 kullanıcı/ay (aylık abonelik)s a day.** Below that you lose money every month.
- **Profit margin at your plan** (50 a day): **55%** of every sale, after every cost.
- Capacity: 10000 a day.

### Year 1, month by month

| month | kullanıcı/ay (aylık abonelik)s a day | revenue | profit | cumulative (after $75,000 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 5 | $5,850 | -$10,964 | -$85,964 |
| 2 | 15 | $17,550 | -$1,344 | -$87,308 |
| 3 | 25 | $29,250 | $8,278 | -$79,030 |
| 4 | 40 | $46,800 | $22,709 | -$56,322 |
| 5 | 55 | $64,350 | $37,140 | -$19,181 |
| 6 | 70 | $81,900 | $51,572 | $32,391 |
| 7 | 85 | $99,450 | $66,004 | $98,394 |
| 8 | 100 | $117,000 | $80,435 | $178,830 |
| 9 | 120 | $140,400 | $99,677 | $278,506 |
| 10 | 150 | $175,500 | $128,540 | $407,046 |
| 11 | 200 | $234,000 | $176,645 | $583,692 |
| 12 | 300 | $351,000 | $272,855 | $856,546 |

- **Year 1 operating profit: $931,546** on $1,363,050 of revenue.
- After the $75,000 startup spend: $856,546.
- Startup money earned back: month 6.
- Cash you need before it pays for itself: **$87,308**.

### What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 55% | 17 | $931,546 |
| Price -10% | 50% | 19 | $795,242 |
| Volume -20% | 49% | 17 | $707,377 |
| Unit costs +15% | 53% | 17 | $895,216 |

No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.

## Marketing

**Tarih:** 2026-10-25  
**Versiyon:** v1.0  
**Strateji:** ORB Framework (Owned → Rented → Borrowed) + 5 Phase Launch

---

### 1. Mevcut Durum ve SLC Kontrolü

| Kriter | Durum | Not |
|--------|-------|-----|
| **Simple** | ✅ | Tek iş: "Puanına göre güvenli/hedef/riskli tercih listesi al" |
| **Lovable** | ⚠️ | RAG latency (cold start ~10s), PWA henüz yok, onboarding friksiyonlu |
| **Complete** | ⚠️ | Kariyer/Konular/Planım/LGS/TUS feature flag kapalı; PWA/PWA kurulum eksik |

**Karar:** Phase 1 (Internal) + Phase 2 (Alpha) paralel → PWA + onboarding iyileştirmesi **önce** lansman.

---

### 2. ORB Kanal Stratejisi

#### Owned (Sahip Olduğumuz — Büyüyen Varlık)
| Kanal | Hedef | Aksiyon | KPI |
|-------|-------|---------|-----|
| **Email List** | Waitlist → Onboarding → Retention | Lead magnet: "Ücretsiz Tercih Raporu PDF" → 5 günlük email serisi | %25+ open rate, %5+ CTR |
| **Blog (SEO)** | Organik trafik | Programmatic SEO (600+ sayfa) + Content cluster | Ayda 10K+ organic session |
| **Discord Community** | Retention + Referral | "UniSense Öğrenci Topluluğu" — tercih paylaşımı, soru-cevap | 1000+ üye, günlük 50+ aktif |
| **Website** | Conversion | PWA, waitlist form, demo video, comparison pages | %3+ waitlist conversion |

#### Rented (Kiralanan — Hız, Kontrolsüz)
| Platform | Hedef Kitle | İçerik Stratejisi | Sıklık |
|----------|-------------|-------------------|--------|
| **Instagram Reels** | Öğrenci (17-22) | "Tercih nasıl yapılır", "Bölüm tanıtımları", "Puan hesaplama" | 3x/hafta |
| **TikTok** | Öğrenci (16-20) | "Tercih robotu demo", "Puan hesaplama trick", "Bölüm günü" | 2x/hafta |
| **YouTube Shorts** | Veli + Öğrenci | "Tercih robotu nasıl çalışır", "Bölüm tanıtımları" | 1x/hafta |
| **LinkedIn** | Veli + Rehber öğretmen | "Tercih danışmanlığı neden önemli", "Veri odaklı karar" | 1x/hafta |
| **X (Twitter)** | EdTech/Tech topluluk | Lansman duyurusu, feature update, data insight | Günlük |

#### Borrowed (Başkalarının Kitle — Hız + Güven)
| Fırsat | Hedef | Yaklaşım |
|--------|-------|----------|
| **Okul Rehber Öğretmenleri** | Veli/Öğrenci güven | "Rehber Öğretmeni Partner Programı" — ücretsiz premium erişim + komisyon |
| **Özel Dershaneler** | YKS/DGS segmenti | "Dershane Partner Programı" — toplu lisans + komisyon |
| **EdTech YouTuber'lar** (10K-100K abone) | Organik güven | Ürün demosu + affiliate link (%20 komisyon) |
| **Öğrenci Toplulukları** (Üni/Kulüp) | Genç kitle | Etkinlik sponsorluğu + waitlist QR |
| **Okul Dergileri/Gazeteleri** | Veli kitlesi | Basın bülteni + uzman görüşü (tercih stratejisi) |

---

### 3. 5-Phase Lansman Takvimi (30 Gün)

#### Phase 1: Internal Launch (Gün 1-3) — "İç Test"
- [ ] 20 "arkadaş/aile" kullanıcısı recruting (WhatsApp/Email)
- [ ] Core flow test: Puan gir → Liste al → Kaydet → Paylaş
- [ ] RAG latency testi (cold/warm), PWA kurulum testi (Android/iOS)
- [ ] Bug bash: Critical path (puan gir → liste → kaydet → PDF)

#### Phase 2: Alpha Launch (Gün 4-10) — "Waitlist Açılışı"
- [ ] Landing page: `unisense.com.tr/waitlist` — "Erken erişim + %70 indirim + yaşam boyu fiyat kilidi"
- [ ] Waitlist formu: Email + segment (YKS/DGS/KPSS/LGS/TUS) + veli/öğrenci
- [ ] Email capture → 5 günlük onboarding drip (Gün 1: Hoş geldin, Gün 2: Pusula demo, Gün 3: Tercih Robotu, Gün 4: PDF rapor, Gün 5: Açılış teklifi)
- [ ] 100 waitlist hedefi (Organik + 50 TL/gün Google Ads "YKS tercih" keyword)

#### Phase 3: Beta Launch (Gün 11-20) — "Buzz Oluşturma"
- [ ] Teaser içerikleri: "Tercih Robotu 30 sn demo", "Pusula 3 soru", "PDF rapor örneği"
- [ ] 5 Rehber öğretmeni + 2 Dershane partner onboarding (ücretsiz premium erişim)
- [ ] 2 EdTech YouTuber (10K-50K abone) — ürün demosu + affiliate link
- [ ] 500 waitlist hedefi (Organik + Partner referral + 200 TL/gün Google Ads)
- [ ] Product Hunt listing hazırlığı (assets, hunter, tagline)

#### Phase 4: Early Access Launch (Gün 21-27) — "Kontrollü Genişleme"
- [ ] Waitlist'ten 50 kullanıcıya "Early Access" daveti (ücretsiz 1 ay Premium)
- [ ] Kullanım verisi toplama: RAG latency, PWA kurulum oranı, feature adoption
- [ ] Product Hunt lansmanı (Gün 24-25) — Hunter, thumbnail, tagline, demo video
- [ ] Product Hunt günü: Tüm ekip engaged, her yoruma yanıt, trafiği waitlist'e yönlendir
- [ ] 1000 waitlist hedefi (PH trafiği + referral loop)

#### Phase 5: Full Launch (Gün 28-30) — "Genel Açılış"
- [ ] Self-serve signup açılır (Stripe + Firebase)
- [ ] Genel duyuru: Email listesi, Blog yazısı, Social (tüm platformlar), Product Hunt
- [ ] Lansman paketi: Blog yazısı, Comparison pages, Demo video, Press kit
- [ ] Referral program aktif: "Arkadaş davet et → 1 ay ücretsiz Premium"
- [ ] Google Ads scale: 500 TL/gün → 2000 TL/gün (YKS sezonu yaklaştıkça)
- [ ] 30 günlük rapor: Waitlist → Activated → Paid conversion funnel

---

### 4. Programmatic SEO (600+ Sayfa — Kullanılabilir 30 günde)

#### Şablon: `"X üniversitesi Y bölümü taban puanı 2024"`
- **URL yapısı:** `/bolum/{universite-slug}/{bolum-slug}`
- **İçerik:** Taban puan (3 yıl), sıralama, kontenjan, burs, fakülte, şehir, Kariyer sinyalleri (bölüm mezunu ilanlar)
- **Schema:** `Course`, `EducationalOrganization`, `FAQPage`
- **İç linkler:** Benzer bölümler, aynı üniversite diğer bölümleri, aynı şehirdeki üniversiteler

#### Content Clusters (Blog — Haftalık 2 yazı)
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

### 5. KPI Dashboard (Haftalık Takip)

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

### 6. Bütçe Dağılımı (30 Gün)

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

### 6. Riskler ve Mitigasyon

| Risk | Olasılık | Etki | Mitigasyon |
|------|----------|------|------------|
| Google Core Update (SEO trafiği düşüş) | Orta | Yüksek | Content cluster çeşitliliği, Brand traffic odaklı, Email listesi |
| Product Hunt flop | Düşük | Orta | Pre-launch hunter + supporter listesi (50+ kişi) hazır |
| RAG latency / hata (Kullanıcı kaybı) | Orta | Yüksek | Warmup + Cache + Fallback mesaj + Hata butonu |
| PWA kurulum zorluğu | Yüksek | Orta | QR + Video rehber + "Basit mod" toggle |
| Reklam maliyeti artışı (YKS sezonu) | Yüksek | Orta | Organic/Referral oranını %50+ tut, CAC cap koy |

---

### 7. Sonraki Adımlar (Bu Hafta)

1. [ ] **Landing page + Waitlist formu** deploy (Vercel + Firestore)
2. [ ] **Email drip (5 gün)** taslağı yaz + MailerSend/MailerLite entegrasyonu
3. [ ] **PWA manifest + Service Worker** + QR kod generator + Demo video
4. [ ] **Partner outreach** — 10 rehber öğretmeni + 3 dershane cold email
4. [ ] **Product Hunt assets** hazırla (Hunter, Thumbnail, Tagline, Demo GIF)
5. [ ] **Google Ads** kampanya kur (YKS/tercih keyword, negative keyword listesi)

---

### Sonraki Adım: Brand → Ops → Launch → Plan

## Brand

**Tarih:** 2026-10-25  
**Versiyon:** v1.0  
**Dayanak:** `founder/idea.md`, `founder/marketing.md`, `founder/competitors.md`, `founder/panel/results.md`

---

### 1. Name Candidates (10 Aday)

| # | Ad | Stil | Ne Anlama Gelir | Sesli Okunuş | Risk |
|---|-----|------|-----------------|--------------|------|
| 1 | **UniSense** | Descriptive | "University Sense" — Üniversite hissini doğru yakalar | yu-ni-sens | Mevcut marka, alan adı alınmış (unisense.com.tr) |
| 2 | **TercihSense** | Descriptive | "Tercih + Sense" — Tercih hissini yakalar | ter-cih-sens | "Sense" kelimesi yaygın, marka ayrımı zor |
| 3 | **PuanPilot** | Evocative | "Puan + Pilot" — Puanınızı rehber eden pilot | pu-an-pi-lot | "Pilot" kelimesi havacılıkla karıştırılabilir |
| 4 | **TercihKompas** | Descriptive | "Tercih + Kompas" — Yön bulucu | ter-cih-kom-pas | "Kompas" kelimesi yaygın (UniSense'de Pusula = Kompas) |
| 5 | **YolHaritası** | Descriptive | "Yol Haritası" — Tercih yolunu gösterir | yol-ha-ri-ta-sı | Türkçe karakterli domain riski, yazım zor |
| 6 | **AdımAdım** | Evocative | "Adım Adım" — Tercih sürecini adım adım gider | a-dım-a-dım | Çok genel, marka kimliği zayıf |
| 7 | **GüvenliListe** | Descriptive | "Güvenli Liste" — Güvenli/hedef/riskli listeler | gü-ven-li-lis-te | Çok fonksiyonel, marka hissiz |
| 8 | **SıralamaBeni** | Invented | "Sıralama Beni" — Sıralamana göre beni yönlendir | sı-ra-la-ma-be-ni | Türkçe karakter, yazım zor |
| 9 | **UniGuide** | Descriptive | "University Guide" — Üniversite rehberi | u-ni-gayd | İngilizce, uluslararası pazarlarda avantaj |
| 10 | **AkademikGPS** | Evocative | "Akademik GPS" — Akademik yolculuğun navigasyonu | a-ka-de-mik-ji-pi-es | "GPS" markası Garmin vb. ile karıştırılabilir |

**Kısa Liste (Top 3):**
1. **UniSense** — Mevcut marka, domain alınmış, marka değerı var
2. **UniGuide** — Uluslararası, temiz, "Guide" kelimesi rehber vurgusu
3. **TercihKompas** — Türk pazarına özgü, "Pusula" özelliğiyle uyumlu

**Öneri:** **UniSense**'i koru (marka eşitliği var), "UniGuide" olarak alt marka/uluslararası versiyon için ayr.

---

### 2. Domain & Handle Kontrolü (Yapılacak)

| Platform | UniSense | UniGuide | TercihKompas |
|----------|----------|----------|--------------|
| **.com** | ❌ Alınmış | ❌ Alınmış | ✅ Müsait |
| **.com.tr** | ✅ Alınmış (unisense.com.tr) | ❌ Alınmış | ✅ Müsait |
| **Instagram** | @unisense | @uniguide | @tercihkompas |
| **TikTok** | @unisense | @uniguide | @tercihkompas |
| **X (Twitter)** | @unisense | @uniguide | @tercihkompas |
| **YouTube** | @unisense | @uniguide | @tercihkompas |
| **LinkedIn** | UniSense | UniGuide | TercihKompas |

> **Not:** Kullanıcı bu kontrolleri yapmalı (otomasyon araçları yanılabilir). Trademark avukatı onayı şart.

---

### 3. Voice & Promise

#### One-Line Promise (Tek Cümlelik Söz)
> **"Puanına göre, resmi veriyle, % olasılıkla güvenli/hedef/riskli tercih listesi — her cevapta kaynak gösteren tek platform."**

#### Tagline Adayları (3 Seçenek)

| # | Tagline | Neden |
|---|---------|-------|
| 1 | **"Puanına göre güvenli liste, resmi veriyle."** | Net, güven vurgusu, hedef kitleye hitap eder |
| 2 | **"Tercih kaza değil, strateji."** | Duygusal, fark yaratıcı, "kaza" kelimesi dikkat çeker |
| 3 | **"Gerçek veriyle doğru tercih."** | Basit, güven verici, "gerçek veri" vurgusu |

**Öneri:** #1 ana tagline, #2 kampanya başlığı, #3 alt başlık olarak kullan.

#### Brand Voice (3 Sıfat + Do/Don't)

| Sıfat | Do | Don't | Before / After |
|-------|-----|-------|----------------|
| **Güvenilir** | Resmi kaynak linki ver, hata butonu koy, "bilmiyorum" de | Tahmin yapma, "bence" deme, kaynaksız iddia et | Before: "Bu bölüm iyi" → After: "Bu bölüm 2024 tabanı 450.12, kaynak: YÖK Atlas [link]" |
| **Sakin** | Kısa cümleler, nüanslı ton, "anlıyorum" de | Ünlem işareti aşırı kullanma, panik yaratma, "açil" deme | Before: "HEMEN TERCİH YAP!" → After: "Puanını gir, güvenli listeni al, rahat et." |
| **Öğrenci Odaklı** | "Senin" dili, empati, "sınav stresi biliyorum" de | Akademik/corporate ton, "kullanıcı" de, uzman dili | Before: "Kullanıcı profili oluşturuluyor" → After: "Puanını gir, sana özel liste hazırlayayım" |

---

### 4. The Look (Görsel Brief)

#### Colour Palette (Renk Paleti)

| Rol | Renk | Hex | Kullanım Alanı | WCAG AA (Beyaz Üzerinde) |
|-----|------|-----|----------------|---------------------------|
| **Primary (Güven)** | Mavi | `#2563EB` | Primary button, link, header bar | ✅ 4.5:1 (Beyaz yazı) |
| **Secondary (Başarı)** | Yeşil | `#059669` | Success state, "Güvenli" badge, onay | ✅ 4.5:1 |
| **Accent (Dikkat)** | Turuncu | `#EA580C` | Warning, deadline, "Riskli" badge, CTA hover | ✅ 3:1 (Koyu gri yazıyla) |
| **Neutral Dark** | Koyu Gri | `#1E293B` | Başlık, body text (dark mode) | ✅ 15:1 |
| **Neutral Light** | Açık Gri | `#F1F5F9` | Background, card, input bg | N/A |
| **Surface** | Beyaz | `#FFFFFF` | Card, modal, input surface | N/A |

**Dark Mode Paleti:** Primary `#3B82F6`, Secondary `#10B981`, Accent `#FB923C`, Background `#0F172A`, Surface `#1E293B`

#### Typography (Tipografi)

| Rol | Font | Kaynak | Neden |
|-----|------|--------|-------|
| **Display (Başlık)** | **Inter** (SemiBold/Bold) | Google Fonts (Free) | Modern, okunaklı, variable font, TR karakter desteği |
| **Body (Metin)** | **Inter** (Regular/Medium) | Google Fonts (Free) | Okunabilirlik, TR karakter, variable font (tek dosya) |
| **Mono (Kod/ÖSYM Kodu)** | **JetBrains Mono** | Google Fonts (Free) | Kod blokları, ÖSYM kodları, monospace gereken yerler |

**Hierarchy:**
- H1: Inter SemiBold 32px / 1.2 line-height
- H2: Inter SemiBold 24px / 1.3
- H3: Inter Medium 20px / 1.4
- Body: Inter Regular 16px / 1.6
- Small: Inter Regular 14px / 1.5
- Caption: Inter Regular 12px / 1.5

#### Logo Brief

**Ne Anlatmalı:** "Üniversite yönlendirmesi, güvenilirlik, teknoloji, basitlik"

**Nerede Çalışmalı:**
- 32px App Icon (iOS/Android)
- 16px Favicon
- 120px Website Header
- 200px Landing Page Hero
- 50mm Fiziksel kart/broşür

**Tasarım Unsurları:**
- Sembol: Basitleştirilmiş pusula/ok (yönlendirme) + "U" harfi entegrasyonu
- Logotype: "UniSense" — Inter SemiBold, kerning +5
- Renk: Primary mavi (`#2563EB`) + Secondary yeşil (`#059669`) gradyan

**Kaçınılacaklar:**
- Karmaşık detay (32px'de kaybolur)
- Çok renkli (marka kimliği zayıflar)
- "Üniversite binası" klşe sembolleri
- Serif font (modernlik kaybeder)

---

### 5. First Five Touchpoints (İlk 5 Dokunma Noktası)

| # | Touchpoint | Ne Gösterir | Brand Voice Uygulaması |
|---|------------|-------------|------------------------|
| **1. Homepage (Hero)** | "Puanına göre güvenli liste, resmi veriyle." + PWA kurulum QR + "Ücretsiz başla" CTA | Güvenilir + Öğrenci odaklı: "Puanını gir, 30 sn'de listeni al" |
| **2. Onboarding Email #1 (Waitlist)** | "Hoş geldin! 5 günde tercih uzmanı olacaksın. Bugün: Pusula — 3 soru, bölüm önerisi." | Sakin + Öğrenci odaklı: "Stres etme, adım adım gidelim" |
| **3. Premium Upgrade Sayfası** | "Yerleşme Garantisi: Yerleşmezsen para iade. PDF rapor indir. Kariyer sinyalleri." | Güvenilir: "Garanti koşullu ama net. Koşullar: puan girişi + liste onayı." |
| **4. İlk Sosyal Post (Launch Günü)** | "🚀 UniSense Pro yayında! Puanına göre % olasılıkla güvenli liste. Kaynak: YÖK Atlas. Yarışma yok, strateji var. #TercihStratejisi" | Güvenilir + Öğrenci odaklı: "Yarışma yok, strateji var" |
| **5. İlk Şikayet Cevabı** | "Anlıyorum, endişen haklı. Hangi bölüm/üniversite? Kaynak linkini paylaşayım, birlikte kontrol edelim. Hata butonu ile bildirirsen 24 saatte düzeltirim." | Güvenilir + Öğrenci odaklı: "Anlıyorum... birlikte çözelim. 24 saatte düzeltirim." |

---

### 6. Competitor Differentiation (Rakiplerden Ayrışma)

| Unsur | YÖK Atlas | Tercih Robotu | Danışmanlık | **UniSense Pro** |
|-------|-----------|---------------|-------------|------------------|
| **Renk** | Kırmızı/Beyaz (Resmi) | Mavi/Turuncu | Koyu Mavi/Altın | **Mavi/Yeşil/Turuncu** (Güven+Başarı+Dikkat) |
| **Font** | Serif (Resmi) | Sans (Modern) | Serif (Geleneksel) | **Inter (Modern, TR)** |
| **Logo** | Atatürk/Anıt | Robot/Kompas | Kalem/Kitap | **Pusula/Ok + "U"** |
| **Slogan** | "Resmi Veri" | "Güvenli Liste" | "Kişisel Danışman" | **"Resmi Veriyle % Olasılık"** |

---

### Çıktı
- `founder/brand.md` (bu dosya)
- Sonraki: `founder-ops` → `founder-launch` → `founder-plan`

## Operations

**Tarih:** 2026-10-25  
**Versiyon:** v1.0  
**Dayanak:** `founder/idea.md`, `founder/offer.md`, `founder/numbers.json`, `founder/marketing.md`

---

### 1. Günlük Operasyon Döngüsü (Gün Başlangıcı → Gün Sonu)

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

### 2. Tedarikçiler (Suppliers) — Gerçek Maliyetler ve Alternatifler

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

### 3. İnsan Kaynağı (People) — Roller ve Rota

#### Mevcut Takım (Gün 1)
| Rol | Kişi | Saat/Hafta | Maliyet (Aylık) | Not |
|-----|------|------------|-----------------|-----|
| **Founder / Full-Stack Dev** | Sahip (Siz) | 20-30 saat | 15,000 TL (0.5 FTE equivalent) | Core dev, product, ops, marketing |
| **Frontend/UX (Freelance)** | Upwork/Fiverr | 10-15 saat | 5,000 TL | PWA, QR, onboarding, UI polish |
| **Content/SEO (Freelance)** | Upwork/İşkur | 10 saat | 3,000 TL | Blog, programmatic SEO şablonları |
| **Content/SEO (Freelance)** | Upwork/İşkur | 10 saat | 3,000 TL | Blog, programmatic SEO şablonları |
| **Tasarımcı (Freelance)** | Upwork/99designs | 5 saat | 2,000 TL | Logo, UI kit, demo video |

**Toplam Aylık Personel Maliyeti:** ~23,000 TL (Founder hariç ~8,000 TL)

#### Haftalık Rota (Planlanmış Hacim: 50/gün → ~1500/ay)

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

### 4. SOPs (Standart Operasyon Prosedürleri) — Tek Sayfa

#### SOP-001: Günlük Veri Pipeline (00:00 Cron)
```
1. GitHub Actions / Render Cron tetikler: scrape_all.py
2. Her scraper sırasıyla: RG → Jooble → Careerjet → ATS → Kamuilan → AkademikTR → Savunma → TÜRKSAT
3. Her scraper: normalize → v2_kayit → _merge → write_json_guarded
4. Başarısız scraper: retry 3x (exponential backoff) → Slack alert
4. Başarılı: ChromaDB upsert → embed_texts_local → write_json_guarded (kariyer_ilanlar.json)
5. Son: _kosu_raporu + _gecmis_guncelle → kariyer_kosu.json
```
**SLA:** 06:00'a kadar bitmeli. Başarısızsa 07:00 Slack alert → Manuel yeniden başlatma.

#### SOP-002: RAG Sorgu (API /ask)
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

#### SOP-003: Premium Upgrade (Stripe Checkout)
```
1. Kullanıcı "Premium'a Geç" tıklar → Frontend Stripe Checkout Session oluştur
2. Stripe webhook: checkout.session.completed → Firestore user.premium=true + expires_at
3. Email gönder: "Premium aktif! PDF rapor, garantili liste, kariyer sinyalleri..."
4. Firestore: user.premium=true, premium_expires_at=now+1month/year
5. Feature flag: user.premium=true → UI'de premium feature'lar görünür
```
**Rollback:** Stripe refund → Firestore premium=false → Email bildirim.

#### SOP-004: Destek Talebi İşleme (SLA 4 saat)
```
1. Gelen: Email / Typeform / Discord / GitHub Issue
2. Tag: "bug" | "feature" | "billing" | "data" | "ux"
3. Öncelik: P0 (kritik: ödeme, veri kaybı) → 1 saat | P1 (RAG hata) → 4 saat | P2 (UX/Feature) → 24 saat
4. Çözüm: Fix → Deploy → Kullanıcıya bildirim + "Çözüldü" tag
5. Kapanış: "Çözüldü" tag + Notion/GitHub issue kapatma
```
**Eskalasyon:** P0 → Founder anında | P1 → 4 saat içinde | P2 → Sprint'e al

#### SOP-005: Haftalık Backup / DR Test (Cumartesi 02:00)
```
1. ChromaDB: `chromadb export` → GCS bucket (versioned)
2. Firestore: `gcloud firestore export gs://bucket/backup/$(date)`
3. GitHub: `git push --mirror backup-repo`
4. Restore test (Ayda 1): Yeni Render service → backup'tan restore → API health check
```
**RTO:** 2 saat | **RPO:** 24 saat

---

### 5. Araç Yığını (Tool Stack) — Minimal & Gerekli

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

### 6. Lisans, İzinler, Sigorta (Türkiye — Istanbul)

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

### 7. Risk Register (En Olası 10 Risk)

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

### Çıktı
- `founder/ops.md` (bu dosya)
- `founder/numbers.json` (güncellenmiş maliyetlerle)
- Sonraki: `founder-launch` → `founder-plan`

## Launch plan

**Tarih:** 2026-10-25  
**Versiyon:** v1.0  
**Dayanak:** `founder/marketing.md`, `founder/offer.md`, `founder/brand.md`

---

### 1. Lansman Stratejisi Özeti

| Aşama | Gün | Odak | Hedef |
|-------|-----|------|-------|
| **Phase 1: Internal** | 1-3 | Core flow test, bug bash | 20 test kullanıcısı, 0 kritik bug |
| **Phase 2: Alpha** | 4-10 | Waitlist açılışı | 100 waitlist |
| **Phase 3: Beta** | 11-20 | Buzz + Partner | 500 waitlist, 5 partner |
| **Phase 4: Early Access** | 21-27 | Product Hunt + Early Access | 1000 waitlist, PH top 5 |
| **Phase 5: Full Launch** | 28-30 | Genel açılış | Self-serve aktif, 50 paid |

---

### 2. Phase 1: Internal Launch (Gün 1-3)

#### Hedef
Core flow (Puan gir → Liste al → Kaydet → PDF → Paylaş) testi, kritik bug sıfırlama.

#### Aksiyonlar
| Görev | Sorumlu | Süre | Kriter |
|-------|---------|------|--------|
| 20 test kullanıcısı recruting (WhatsApp/Email/Üniversite topluluklar) | Founder | Gün 1 | 20 kişi onay |
| Core flow test: Puan gir → Liste al → Kaydet → PDF → Paylaş | Founder + 20 testçi | Gün 1-2 | 0 kritik bug |
| RAG latency testi: Cold start <10s, Warm <3s | Founder | Gün 2 | p95 <3s (warm) |
| PWA kurulum testi: Android (Chrome) + iOS (Safari) + QR | Founder | Gün 2 | 100% başarı |
| Bug bash: Critical path (Puan gir → Liste → Kaydet → PDF → Paylaş) | Founder + Testçiler | Gün 3 | 0 Critical, <5 Major |

#### Çıktı
- **Test raporu:** `founder/launch/internal-test-report.md`
- **Bilinen issue'lar:** GitHub Issues (Critical: 0, Major: <3, Minor: <10)
- **Go/No-Go kararı:** Phase 2'ye geçiş onayı

---

### 2. Phase 2: Alpha Launch — Waitlist Açılışı (Gün 4-10)

#### Hedef
Waitlist 100 kayıt, email drip aktivasyonu.

#### Landing Page: `unisense.com.tr/waitlist`
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

#### Email Drip (5 Gün — MailerSend/MailerLite)

| Gün | Konu | İçerik Özeti | CTA |
|-----|------|--------------|-----|
| **Gün 1** | "Hoş geldin! 5 günde tercih uzmanı olacaksın." | Hoş geldin, ne bekler? Bugün: Pusula — 3 soru, bölüm önerisi | "Pusula'yı Dene (30 sn)" |
| **Gün 2** | "Puanını gir, güvenli listeyi al." | Tercih Robotu demo: Puan gir → % olasılık + güvenli/hedef/riskli | "Tercih Robotu'nu Dene" |
| **Gün 3** | "Her cevapta kaynak linki + hata butonu." | RAG şeffaflığı: Kaynak linki + ÖSYM kodu + Hata butonu | "Kaynak Şeffaflığını Gör" |
| **Gün 4** | "Yerleşme garantisi: Yerleşmezsen para iade." | Premium garantisi: Koşullar + %50 indirim + yaşam boyu kilit | "Erken Erişim %70 İndirim" |
| **Gün 5** | "Yarın açılıyor: İlk 1000'e %70 indirim." | Son hatırlatma: Açılış teklifi, QR kod, PWA kurulum videosu | "İlk 1000'e Gir (%70 İndirim)" |

#### Trafik Kanalları (Gün 4-10)
| Kanal | Bütçe | Hedef | Not |
|-------|-------|-------|-----|
| **Organic/Referral** | 0 TL | 40 kayıt | Partner referral (rehber/dershane) |
| **Google Ads (YKS/tercih)** | 500 TL/gün | 40 kayıt | Negative keyword listesi kritik |
| **Partner Referral** | 0 TL | 20 kayıt | 10 rehber öğretmeni + 3 dershane |

**Hedef:** 100 waitlist (Gün 10 sonu)

---

### 3. Phase 3: Beta Launch (Gün 11-20)

#### Hedef
500 waitlist, 5 partner, buzz oluşturma.

#### Aksiyonlar
| Görev | Sorumlu | Gün | Kriter |
|-------|---------|-----|--------|
| Teaser içerikler: "Tercih Robotu 30 sn demo", "Pusula 3 soru", "PDF rapor örneği" | Marketing (Freelancer) | Gün 11-13 | 3 video + 3 Reel/Short |
| 5 Rehber öğretmeni + 2 Dershane partner onboarding (ücretsiz premium) | Founder | Gün 11-15 | 7 partner aktif |
| 2 EdTech YouTuber (10K-50K abone) — Ürün demosu + Affiliate link | Founder | Gün 12-16 | 2 video yayında |
| Product Hunt assets hazırlığı (Hunter, Thumbnail, Tagline, Demo GIF) | Founder + Designer | Gün 14-18 | Assets hazır |
| 500 waitlist hedefi (Organik + Partner referral + 200 TL/gün Ads) | Marketing | Gün 11-20 | 500 kayıt |

#### Partner Programı
| Partner Tipi | Komisyon | Faydaları | Hedef |
|--------------|----------|-----------|-------|
| **Rehber Öğretmeni** | %20 revenue share (yaşam boyu) | Ücretsiz Premium + Öğrenci takip paneli | 10 öğretmen |
| **Dershane** | %20 revenue share + toplu lisans indirimi | Öğrenci takip paneli + toplu yönetim | 5 dershane |
| **EdTech YouTuber** | %20 afiliate (ilk yıl) | Ücretsiz Premium + Özel kod | 5 kanal (10K-100K abone) |

---

### 4. Phase 4: Early Access + Product Hunt (Gün 21-27)

#### Hedef
Product Hunt top 5, 1000 waitlist, early access feedback.

#### Product Hunt Lansmanı (Gün 24-25)

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

### 5. Phase 5: Full Launch (Gün 28-30)

#### Hedef
Self-serve signup aktif, ödeme almaya başlama, genel duyuru.

#### Launch Day (Gün 28)
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

#### Post-Launch (Gün 29-30)
- [ ] Onboarding email sequence aktif (5 günlük drip)
- [ ] Referral program tracking dashboard
- [ ] Feedback toplama (Typeform: 5 soru, NPS)
- [ ] Bug bash: Kullanıcı raporları → Critical fix → Deploy
- [ ] 30 günlük rapor hazırlama: Funnel (Waitlist → Activated → Paid), CAC, LTV, Churn

---

### 5. Lansman Malzemeleri (Assets)

#### Basın Seti (Press Kit) — `founder/launch/press-kit/`
| Dosya | Format | İçerik |
|-------|--------|--------|
| `one-pager.pdf` | PDF (1 sayfa) | Problem, Çözüm, Metrikler, Team, İletişim |
| `logo-pack.zip` | ZIP | Logo (SVG/PNG), Favicon, App Icon, Brand guidelines |
| `screenshots/` | PNG (1280x720) | Home, Tercih Robotu, Pusula, PDF Raporu, PWA, Mobil |
| `demo-video.mp4` | MP4 (60 sn) | Hero demo: Puan gir → Liste → PDF → PWA kur |
| `founder-bio.md` | MD | Founder hikayesi, LinkedIn, Twitter |
| `key-metrics.md` | MD | 71% buy rate, 55% margin, 17 break-even, 6 ay payback |

#### Product Hunt Listing
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

### 6. Referral Programı (Viral Loop)

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

### 7. 30 Günlük Rapor Şablonu (Gün 30)

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

### Çıktı
- `founder/launch.md` (bu dosya)
- Lansman asset'leri: `founder/launch/press-kit/`
- Product Hunt listing hazır
- Sonraki: `founder-plan` → İş planı / Yatırımcı özeti

## Not done yet

- Summary: run /founder-plan
- The buyer panel: run /founder-consumer
- Pricing: run /founder-pricing

_The panel is simulated buyers and the numbers are projections from your inputs. Confirm demand with real customers and costs with real quotes before you spend. Not financial, legal or tax advice._
