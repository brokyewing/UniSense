# Kapsama Matrisi — "tek bir site bile kalmasın"

**Ölçüm:** Claude Code, 2026-09-05 · **Amaç:** TR'deki her ilan kaynağını
otomatik toplamak. Bu dosya *nerede olduğumuzu* ve *ne kaldığını* sayıyla söyler.

## Bugünkü durum

| | Sayı |
|---|---|
| Fiilen toplanan kaynak | **7** |
| Kullanıcıya gösterilen rehber | 42 |
| **Yalnız link — otomatik toplanmıyor** | **~35** |

Toplanan 7: `rg`, `kamuilan`, `kariyerkapisi`, `akademiktr`, `ilangovtr`
(kamu) + `jooble`, `careerjet` (özel toplayıcı).

⚠️ **Toplayıcıların kapsamı ÖLÇÜLEMİYOR.** Jooble ve Careerjet ilan
linklerini kendi yönlendirme adresleriyle veriyor (`tr.jooble.org`,
`jobviewtrack.com`); Careerjet API'sinin `site` alanı boş dönüyor (eşleme
doğru — `_careerjet_normalize` zaten `job.get("site")` okuyor, API vermiyor).
Yani "kariyer.net'i dolaylı topluyor muyuz?" sorusunu **veriden cevaplayamıyoruz.**
→ Bu belirsizlik, doğrudan adaptör yazmayı tercih etmek için yeterli sebep.

---

## 1. HEMEN YAPILABİLİR — araştırması bitmiş, kod bekliyor

Bu ikisi tam belgelenmiş durumda; kayıt defterine girip adaptör yazmak yeterli.

| Kaynak | Hazır bilgi | Kazanç |
|---|---|---|
| **savunmakariyer.com** | API tamamen çözüldü (`KAYNAK_HARITASI` §10): `POST /api/career-core/public/jobs`, `GET /api/common/public/city`, `GET /api/corporate/public/approved-companies`. Auth yok. `jobLocation` il, `endDate` son başvuru. | 24 ilan + 343 firma dizini + 81 il. ASELSAN/HAVELSAN/ROKETSAN/STM/BAYKAR/TUSAŞ/TEI dahil. |
| **Lever ATS panoları** | 6 slug doğrulandı (§9.3): `trendyol`, `peakgames`, `dreamgames`, `getmidas`, `iyzico`, `insiderone`. `api.lever.co/v0/postings/<slug>?mode=json`, auth yok. | ~101 TR ilanı. Tek adaptör, N şirket. |

---

## 2. TEKNİK OLARAK MÜMKÜN — araştırma gerekiyor

robots.txt izin veriyor ya da kısmen veriyor; WAF/JS durumu ölçülmeli.

| Kaynak | robots durumu | Not |
|---|---|---|
| kariyer.net | ✅ ilan yolları serbest (`/filtre*`, `/ozgecmis/*` yasak) | TR'nin en büyüğü. WAF ölçülmeli. |
| yenibiris.com | ✅ ilan/arama yolunda yasak yok | RSS yok (404). |
| isbul.net | ölçülmedi | Canlı, mavi yaka ağırlıklı. |
| secretcv.com | 🟡 4 ilan/arama yasağı | Yol bazında bakılmalı. |
| eleman.net | 🟡 4 ilan/arama yasağı | 81 ilde ilan iddiası — bölge kapsamı için değerli. |
| akademikag.com | ölçülmedi | Akademik toplayıcı. |
| tr.indeed.com | 🔴 468 kural, 128'i ilan/arama | TR yolları ayrıca teyit edilmeli. |
| Greenhouse ATS | ✅ açık API | TR şirketi henüz bulunamadı; slug avı sürmeli. |
| Kamu kurum siteleri (TCMB, BDDK, SPK, Sayıştay, MSB, Jandarma, EGM…) | genelde serbest | Her biri ayrı; önce ilanlarının BİK'te görünüp görünmediği ölçülmeli — görünüyorsa adaptör GEREKSİZ. |

---

## 3. KAPALI — otomatik toplanmayacak (rehberde link olarak kalır)

| Kaynak | Sebep |
|---|---|
| **LinkedIn** | `robots.txt`: `User-agent: *` → `Disallow: /`, ayrıca `anthropic-ai` için özel yasak. İzin alınmadan tek satır çekilmez. |
| **İŞKUR e-Şube** | WAF — `robots.txt` bile "Request Rejected". İlanları BİK/Kariyer Kapısı'nda göründüğü için kapsama kaybı sınırlı. |
| e-Devlet arkasındaki listeler | Giriş asla otomatikleştirilmez. |
| kodilan.com | Site artık iş sitesi değil (kumar/oyun). Rehberden silinmeli. |

---

## 4. ÖNCELİK SIRASI (kapsamı en hızlı büyüten)

1. **savunmakariyer** — hazır, 24 ilan + 343 firma, sıfır araştırma
2. **Lever ATS** — hazır, ~101 ilan, tek adaptör N şirket
3. **kariyer.net** — TR'nin en büyüğü, robots ilan yollarına izin veriyor
4. **eleman.net** — "81 ilde ilan" iddiası; bölge kapsamı için en değerlisi
5. **yenibiris + isbul + secretcv** — orta ölçek
6. **Kamu kurum siteleri** — önce BİK'te görünüp görünmediklerini ölç; çoğu için
   adaptör gereksiz çıkabilir

---

## 5. Dürüst sınır

**"Tek bir site bile kalmayacak" tam anlamıyla ulaşılamaz** ve bunu peşinen
söylemek gerekir:

- LinkedIn ve İŞKUR **hukuken/teknik olarak** kapalı.
- Türkiye'de on binlerce şirketin kendi kariyer sayfası var; çoğu KOBİ ve
  kariyer sayfası yok. Kurum-kurum tarama ölçülerek elendi
  (`KAYNAK_HARITASI` §1: ortak URL deseni yok, üniversite siteleri soft-404).
- Ulaşılabilir hedef: **ilanların çoğunun geçtiği kaynakları kapsamak.** Kamu
  tarafında bu neredeyse tamam (BİK yasal zorunlu, 81 il tek merkezden).
  Özel sektörde toplayıcılar + ATS + büyük panolar birleşimi.

Ölçülebilir hedef önerisi: **rehberdeki 42 kaynağın toplanabilir olanlarının
%80'i** — bugün 7/~30 (≈%23).
