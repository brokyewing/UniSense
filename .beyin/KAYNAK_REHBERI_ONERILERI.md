# Kaynak Rehberi — düzeltmeler ve yeni girdiler

**Hazırlayan:** Claude Code (araştırma + doğrulama) · **Tarih:** 2026-09-05
**Uygulayacak:** opencode — `kariyer_service.py` içindeki `_KAYNAKLAR` listesi
onun alanı (`SAHIPLIK.md`), ben dokunmadım.

Mevcut rehber: **42 kaynak** (31 kamu / 11 özel).
Aşağıdakiler canlı yoklamayla doğrulandı; her satırın kanıtı yazılı.

---

## A. ÖNCE DÜZELTİLMESİ GEREKENLER

### A1. 🚨 `kodilan` — SİLİNMELİ (kullanıcıya zarar verir)

```
mevcut: {"id":"kodilan", "url":"https://kodilan.com", "not":"Yazılım ilanları."}
```

Alan adı el değiştirmiş. Ana sayfa başlığı: **"Download & Play BDG Game/BDG Win
to Earn Real Money"**. `/rss` hâlâ geçerli bir RSS döndürüyor ama içi
WordPress'in varsayılan "Hello world!" yazısı (`guid` →
`beta.strixdevelopment.net/winindia`).

→ **Listeden çıkar.** İş arayan birini kumar/oyun sitesine yönlendirmek kabul
edilemez.

### A2. `kariyer-kapisi` — notu yanlış

```
mevcut not: "... e-Devlet girişi gerekir."
```

**İlan listesini görmek için e-Devlet GEREKMİYOR.** `/isealim` girişsiz açılıyor;
e-Devlet bağlantısı yalnızca **başvuru** içindir. Üstelik herkese açık RSS var.

```
onerilen not: "En önemli kanal; sözleşmeli bilişim neredeyse tamamı buradan.
İlanları görmek için giriş GEREKMEZ (e-Devlet yalnız başvuruda).
RSS: https://kariyerkapisi.gov.tr/RSS"
```

### A3. `ilan-gov-tr` — notu yanlış

```
mevcut not: "... Botlara API kapalı."
```

**API açık ve kimlik doğrulamasız.** Daha önce kapalı sanılmasının sebebi
geçersiz bir `sorting` değeriymiş; API geçersiz sıralamada hata vermeden
`numFound: 0` dönüyor.

```
onerilen not: "BİK resmî toplayıcı — kamu kurumları ilanlarını buraya
yayımlamakla YÜKÜMLÜ, 81 il tek merkezden. 25.061 ilan, ~%10,5'i personel alımı."
```

### A4. `ilan-yok` — böyle bir adres yok

`ilan.yok.gov.tr` ne yerel çözümleyicide ne 8.8.8.8'de çözülüyor.
Akademik kadro ilanları **ilan.gov.tr'de**, kendi kategorisinde.

→ Bu girdiyi **C3 ile değiştir**.

### A5. `vizyoner-genc` — site taşınmış

`vizyonergenc.com` artık **`savunmakariyer.com`**'a yönleniyor
("Savunma Kariyer | Savunma Sanayi İş ve Staj İlanları").

→ **C1 ile değiştir.**

### A6. `kamu-sosyal` (LinkedIn) — girdi KALSIN, ama not eklensin

Rehber insanlar içindir; kullanıcının LinkedIn'e bakması sorun değil.
**Ama biz oradan veri ÇEKMEYECEĞİZ** — `robots.txt` tüm siteyi yasaklıyor.

```
onerilen not ek: "(UniSense bu kaynaktan ilan çekmez — sitenin robots kuralı
taramaya kapalı; elle takip edilir.)"
```

---

## B. DOĞRULANDI, DEĞİŞİKLİK GEREKMİYOR

- `kamuilan-net` → `https://kamuilan.net` **doğru** (www'lu alt alan DNS'te yok,
  rehberdeki adres zaten www'suz).
- `iskur` → erişim WAF'lı ama **rehber girdisi olarak geçerli**; kullanıcı
  tarayıcıdan girer. Sürekli işçi başvuruları zaten oradan alınıyor.

---

## C. YENİ GİRDİLER (hepsi canlı doğrulandı)

### C1 — Savunma Kariyer (vizyoner-genc yerine)

```json
{"id":"savunma-kariyer","hat":"kamu","tip":"portal","ad":"Savunma Kariyer",
 "url":"https://savunmakariyer.com",
 "not":"Savunma sanayii ortak portalı (KPSS'siz). Eski adı Vizyoner Genç. ASELSAN, HAVELSAN, TUSAŞ, TEI, ROKETSAN, MKE, FNSS, BAYKAR dahil 343 onaylı firma; ilanlar il bilgisiyle geliyor."}
```

### C2 — ilan.gov.tr Akademik

```json
{"id":"ilan-gov-akademik","hat":"kamu","tip":"portal","ad":"ilan.gov.tr Akademik Personel",
 "url":"https://www.ilan.gov.tr/ilan/kategori/73/akademik-personel-alimlari",
 "not":"Üniversite akademik kadro ilanları (ALES+YDS). Ayrıca kategori 8: kamu-akademik-personel."}
```

### C3 — AkademikAğ (`ilan-yok` yerine)

```json
{"id":"akademikag","hat":"kamu","tip":"toplayici","ad":"AkademikAğ",
 "url":"https://akademikag.com/akademik-ilanlar",
 "not":"Akademik ilan toplayıcısı. Resmî değil; başvuru öncesi orijinal ilana bak."}
```

### C4 — isbul.net

```json
{"id":"isbul","hat":"ozel","tip":"portal","ad":"isbul.net",
 "url":"https://www.isbul.net","not":"Genel iş ve eleman ilanları; mavi yaka ağırlıklı."}
```

### C5 — ATS panoları (şirketlerin kendi ilan panoları)

Doğrulanmış Lever panoları — kullanıcı doğrudan gezebilir:

```json
{"id":"ats-lever-tr","hat":"ozel","tip":"toplayici","ad":"Şirket ATS panoları (Lever)",
 "url":"https://jobs.lever.co/trendyol",
 "not":"Trendyol (27), Peak Games (20), Dream Games (19), Midas (13), iyzico (12), Insider One (117, küresel). Slug'lar: trendyol, peakgames, dreamgames, getmidas, iyzico, insiderone."}
```

### C6 — Uzaktan/online çalışma (kullanıcı 'online iş' filtresi istedi)

```json
{"id":"wellfound","hat":"ozel","tip":"portal","ad":"Wellfound (startup + uzaktan)",
 "url":"https://wellfound.com","not":"Startup ilanları; uzaktan çalışma filtresi güçlü."}
{"id":"remoteok","hat":"ozel","tip":"portal","ad":"RemoteOK",
 "url":"https://remoteok.com","not":"Tamamen uzaktan pozisyonlar; yazılım/tasarım ağırlıklı."}
{"id":"bionluk","hat":"ozel","tip":"portal","ad":"Bionluk (freelance)",
 "url":"https://bionluk.com","not":"Serbest çalışma/proje bazlı; iş ilanı değil, gelir kanalı."}
```

### C7 — Bölgesel işveren dizinleri (ilan değil, KEŞİF kaynağı)

```json
{"id":"osbuk","hat":"ozel","tip":"toplayici","ad":"OSBÜK — Organize Sanayi Bölgeleri",
 "url":"https://www.osbuk.org/view/sayilarlaosb/osbliste.php",
 "not":"418 OSB, 302'si faal, 78/81 ilde. İl bazlı sanayi işvereni haritası; ilan değil, işveren keşfi için."}
{"id":"tobb-sanayi","hat":"ozel","tip":"toplayici","ad":"TOBB Sanayi Veri Tabanı",
 "url":"https://sanayi.org.tr/#/sanayi-veri-tabani",
 "not":"Kapasite raporu olan firmalar; il dağılımı, adres, çalışan sayısı. Ücretsiz üyelik ister. İlan değil, firma dizini."}
```

---

## D. Uygulama notu

- C7'deki iki girdi **ilan kaynağı değil** — rehberde ayrı bir `tip` (ör.
  `isveren_dizini`) altında gösterilmesi kullanıcıyı yanıltmaz.
- C5'teki ATS slug'ları **doğrulama tarihi** ile tutulmalı; panolar kapanabiliyor
  (`papara`, `useinsider`, `colendi` aramada görünüyordu, üçü de artık 404).
- Toplam öneri: **1 silme, 4 not düzeltmesi, 2 değiştirme, 9 yeni girdi**
  → rehber 42 → **50** kaynak.
