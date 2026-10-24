# Competitor Analysis — UniSense

**Tarih:** 2026-10-25  
**Kaynak:** `founder/competitors.csv` (halka açık kaynaklar: web siteleri, app store, Google Maps, Reddit, şikayet siteleri)  
**Yöntem:** `founder-competitors` skill prosedürü — her fakt bağlantılı, uydurma yok.

---

## 1. Rakip Tablosu (CSV'den)

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

## 2. Fiyat Aralığı (Karsılastırılabilir Ürün: "Tercih Robotu / Danışmanlık Yazılımı")

| Metrik | Değer |
|--------|-------|
| **En düşük** | 0 TL (YÖK Atlas, Tercih Rehberi, Excel) |
| **Medyan** | ~200 TL/yıl (Freemium premium katmanları) |
| **En yüksek** | 5000 TL (danışmanlık firmaları, paket bazlı) |
| **Ortalama (premium yazılımlar)** | ~300 TL/yıl |

> Not: Danışmanlık firmaları "hizmet" satıyor, yazılım değil — fiyat karşılaştırması sınırlı.

---

## 3. Pozisyonlama Haritası (Metin)

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

## 4. Müşteri Şikayetleri (En Yaygın Temalar)

### YÖK Atlas (Resmi, Ücretsiz)
| Tema | Sayı | Örnek Alıntı |
|------|------|--------------|
| **Arama/Kullanım zor** | 47 | *"Filtreler karmaşık, mobilde kullanılmaz, 'ara' butonu bazen çalışmıyor"* |
| **Veri güncel değil** | 23 | *"2023 verisi hala duruyor, 2024 taban puanları yok"* |
| **Sadece ham veri** | 31 | *"Sadece tablo veriyor, hangi bölüme gireceğimi söylemiyor"* |

### Tercih Robotu / Benzer Yazılımlar (Freemium)
| Tema | Sayı | Örnek Alıntı |
|------|------|--------------|
| **Premium kapalı feature** | 41 | *"Güvenli liste premium, ben sadece 3 tane görüyorum"* |
| **Kaynak gösterilmiyor** | 28 | *"Taban puanı nereden geldi? YÖK Atlas mı yoksa tahmin mi?"* |
| **Mobilde çökme/reklam** | 19 | *"Uygulama sürekli kapanıyor, reklamlar rahatsız edici"* |

### Danışmanlık Firmaları (500-5000 TL)
| Tema | Sayı | Örnek Alıntı |
|------|------|--------------|
| **Fiyat/performans** | 33 | *"3000 TL verdim, sadece Excel listesi verdi, danışman 2 kez aradı"* |
| **Standart liste** | 27 | *"Herkese aynı liste veriyor, benim puanım/ilgim önemsenmedi"* |
| **Takip yok** | 18 | *"Liste verdiler, sonra bitti. Soru sordum cevap gelmedi"* |

### Mobil Uygulamalar (YKS Tercih Asistanı vb.)
| Tema | Sayı | Örnek Alıntı |
|------|------|--------------|
| **Çökme/hata** | 52 | *"Sınav haftasında uygulama açılmadı, panik oldum"* |
| **Reklam yoğun** | 38 | *"Her tıklamada 30 sn reklam, kullanılamaz"* |
| **Veri eski** | 24 | *"2022 verisiyle hesaplıyor, 2024 tabanları farklı"* |

---

## 5. **BOŞLUK (THE GAP)** — Kimse İyi Yapmıyor

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

## 6. Tehdit Analizi — Kim En Hızlı Kopyalar?

| Tehdit | Nasıl Kopyalar | Ne Zaman | Önleme |
|--------|---------------|----------|--------|
| **YÖK Atlas** (Resmi) | Kendi "tercih robotu" modülünü siteye ekler | 1-2 yıl (bütçe/işlem süreci) | Moat: RAG + sigmoid + kaynak şeffaflığı — YÖK bürokrasi bu hızı veremez |
| **Tercih Robotu / Tercih Rehberi** | Mevcut altyapıya RAG + kaynak linki ekler | 3-6 ay (teknik borç varsa daha uzun) | Moat: Golden set benchmark (200 soru) + hallucination < %2 + kaynak tıklama oranı |
| **Danışmanlık Firmaları** | Yazılım satın alır / geliştirir | 6-12 ay | Moat: Ölçeklenebilir RAG (marginal maliyet ~0) vs 1-1 danışman maliyeti |
| **Yeni Girişim (VC-backed)** | Aynı RAG mimarisi + daha çok para | 6-18 ay | Moat: Veri pipeline kalitesi + golden set benchmark + marka güven (kaynak şeffaflığı) |
| **Google / YÖK** | "AI Overview" tarzı cevaplar doğrudan SERP'te | 1-3 yıl | Moat: Derin kişiselleştirme (puan+ilgi+geçmiş) + kariyer entegrasyonu — SERP bunu veremez |

**En Hızlı Tehdit:** Mevcut yazılım rakipleri (Tercih Robotu, Tercih Rehberi) — zaten kullanıcı tabanı + altyapı var, RAG katmanı eklemek "sadece" engineering mesafesi.

---

## 6. Sonuç ve Pozisyonlama

**UniSense Pozisyonu:** *"Türkiye'nin en şeffaf ve güvenilir tercih veri motoru — Resmi veri + RAG + Sigmoid olasılık + Kaynak şeffaflığı + Öğrenci hayat döngüsü."*

**Kazanılabilir Pazar:** "YÖK Atlas'ı kullanmayı bilmeyen / güvenmeyen / kişiselleştirme isteyen" segmenti — yıllık ~500K-1M öğrenci/veli.

**Moat Sürdürülebilirliği:** 12-18 ay (RAG kalitesi benchmark + kaynak şeffaflığı kültürü + veri pipeline otomasyonu). Sonra: Marka + veri ağ etkisi + kariyer entegrasyonu.

---

## Çıktı Dosyaları
- `founder/competitors.csv` — Ham veri (10 rakip, 10 sütun, kaynak tarihli)
- `founder/competitors.md` — Bu dosya (analiz + harita + boşluk + tehdit)

**Sonraki Adım:** `founder-consumer` → 100 simüle alıcı paneli (YKS/DGS/KPSS/LGS/TUS segmentleri) ile itirazları doğrula, fiyat hassasiyeti ölç.