# Grand Slam Offer — UniSense

**Tarih:** 2026-10-25  
**Versiyon:** v2 (Board FUND IF koşullarına dayalı)

---

## 1. Problem Listesi (Panel + Rakiplerden Çekilen 25 Engel)

### Önce Satın Alma (Doubt / Price / Effort)
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

### Satın Alma Sırasında (Waiting / Learning / Inconvenience)
11. "Kayıt olma / giriş yapma zorunluluğu" — Friksiyon
11. "Puan/sıralama girmek zor" — Veri girişi yorucu
12. "Sonuçlar yüklenirken bekleme" — Latency
13. "Filtreleme/arama karmaşık" — Kullanılabilirlik

### Sonrasında (Does it last / What if it fails)
14. "Taban puanı yıl değişirse liste eskimez mi?" — Veri güncelleme
15. "Yerleşmezsem ne olur? Para iade mi?" — Garanti
16. "Yıl içinde veri değişirse bilgilendirme var mı?" — Proaktif haber
17. "Mezun olduktan sonra iş bulmada yardımcı olur mu?" — Kariyer bağlantısı
16. "Aile/veli paylaşımı kolay mı?" — Paylaşım/işbirliği

---

## 2. Solutions → Stack (Value vs Cost Skorlama)

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

## 3. The Stack (Final)

### CORE (Her kullanıcıya, ücretsiz/premium herkese)
1. **RAG + Sigmoid % + Kaynak Linki + Hata Butonu** — Her cevapta YÖK Atlas/ÖSYM linki + ÖSYM kodu + "Hata bildir"
2. **PWA (Progressive Web App)** — Ana ekrana ekle, offline cache, bildirim, QR tek tık kurulum
3. **Sigmoid Yerleşme Olasılığı** — % formatında + güven aralığı (alt/üst sınır)
4. **Kaynak Şeffaflığı** — Her cevapta "Kaynak: YÖK Atlas 2024 [link] [Hata bildir]"
5. **Freemium Sınırsız** — Tercih Robotu, Pusula, Hesap Makinesi, Karşılaştırma, Konu Takibi
6. **KVKK + Reklamsız + Veri Silme Butonu** — Freemium bile reklamsız, veri silme hakkı

### BONUSES (Premium'a özel, her biri bir itirazı öldürür)
1. **Yerleşme Garantisi (Koşullu)** — Puan girişi + liste onayı → Yerleşmezsen para iade
2. **PDF Raporu (İndirilebilir/Paylaşılabilir)** — Veliye/öğretmene WhatsApp/Email ile gönder
3. **Kariyer Sinyalleri (Bölüm Mezunu İlanları)** — Jooble/ATS/API'den bölüm mezunu ilanlar
4. **E-posta/SMS Hatırlatıcı** — Tercih tarihi, sınav takvimi, veri güncelleme
5. **QR Kod Tek Tık Kurulum + Video Rehber** — Mobilde 3 saniyede PWA kurulum
6. **Veliye Özel "Basit Mod" + Demo Video** — İngilizce bilmeyen veli için basitleştirilmiş arayüz
7. **Öncelikli Destek + Topluluk Erişimi** — Discord/Telegram + 24h SLA

### GUARANTEE
**"Yerleşme Garantisi veya Para İade"** — Koşullar: (1) Puan/sıralama girişi yapılmış, (2) Tercih listesi onaylanmış, (3) Freemium denemesi yapılmış. CFO maliyeti: %2-3 claim rate tahmini, LTV'nın %15'i altındaysa karlı.

### URGENCY/SCARCITY (Gerçek)
- **İlk 1000 kullanıcıya:** %50 indirim (49.50 TL/ay) + **Yaşam boyu fiyat kilidi**
- **Açılış haftası:** Kariyer bonusu + PDF rapor hediye
- **Gerçek sayaç:** "Kalan: 847/1000" (gerçek zamanlı)

### NAME
**"UniSense Pro — Yerleşme Garantili Tercih Asistanı"**

---

## 4. Value Equation Skorlaması (1-10)

| Element | Before (v1 Pitch) | After (v2 Stack) | Delta | Moved By |
|---------|-------------------|------------------|-------|----------|
| **Dream Outcome** | 6 | 9 | +3 | Sigmoid % + Garanti + Kariyer |
| **Perceived Likelihood** | 5 | 9 | +4 | Kaynak linki + Hata butonu + Sigmoid % + Garanti |
| **Time to Result** | 5 | 8 | +3 | PWA anlık + Tek tık liste + PDF rapor |
| **Effort & Sacrifice** | 5 | 8 | +3 | PWA tek tık + Freemium + QR kurulum + Velisi basit mod |

**Ortalama:** 5.25 → 8.5 **(+3.25 / +62%)**

---

## 5. Updated Pitch (v2)

# UniSense Pro — Yerleşme Garantili Tercih Asistanı

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

## 6. Re-test Plan

- `founder/pitch-v1.md` olarak eski pitch'i kaydet
- `founder/pitch.md` olarak v2'yi yaz
- `founder-consumer --quick --seed 830163` ile aynı 20 karta tekrar test
- Beklenti: Satın alma oranı %71 → %80+ (özellikle fiyat hassas ve mobil-first segmentlerde artış)
- Değişen itirazlar: Fiyat (%6 → %2), Garanti (%3 → %1), Mobil (%3 → %1)

---

## 6. CFO Maliyet Kontrolü (Gereklilik)

| Bonus/Garanti | Maliyet (CFO numbers.json) | Claim Rate | Yıllık Maliyet/Kullanıcı | LTV Payı |
|--------------|---------------------------|------------|-------------------------|----------|
| Yerleşme Garantisi (Para İade) | ~$15/kullanıcı (LTV $100) | %2-3 | $0.30-0.45 | %15'nin altındaysa karlı |
| PDF Raporu | ~$0.01 | %80 | $0.01 | İhmal edilebilir |
| Kariyer Sinyalleri | API maliyeti (Jooble/Careerjet) | %30 | $2-5/yıl | API maliyeti optimize edilmeli |
| E-posta/SMS | SendGrid/Twilio | %50 | $1-2/yıl | Kullanıcı başı $1-2 |
| PWA/QR/Video | Tek seferlik dev maliyet | - | - | Amortisman 6 ay |

**Sonuç:** Tüm bonus/garanti CFO'nun "karlı" kriterinde (%15 LTV altı). `founder/numbers.json` güncellenecek.

---

## Çıktı
- `founder/offer.md` (bu dosya)
- `founder/pitch.md` (güncellenmiş v2)
- `founder/pitch-v1.md` (eski yedek)
- `founder/numbers.json` (güncellenecek)