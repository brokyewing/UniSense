# Devir — UniSense
**Son araç:** Claude Code
**Tarih:** 2026-09-05 10:30
**Durum:** calisiyor

> ⚠️ opencode aynı repoda **eşzamanlı** çalışıyor (Kariyer fazları). Dosya
> çakışması yaşandı ve veri kaybına yol açtı (bkz. "Dersler"). Aynı dosyaya
> yazmadan önce `git status` bak.

## Nerede kaldık

### Bu oturumda bitenler (kronolojik)

**Altyapı / kalite**
- keep-alive: GitHub cron ölçüldü (istenen 10 dk, gerçek 108-273 dk). Workflow
  55 dk boyunca 5 dk arayla pingliyor. Asıl çözüm cron-job.org — kullanıcı
  kurdu, **çalışıyor** (backend 1 sn'de cevap veriyor).
- Hiç yeşil görmemiş 3 sync workflow onarıldı (eksik paket kurulumu, beyan
  edilmemiş `yokatlas-py`, eksik `--target`). Dördü de dispatch ile YEŞİL
  koştu: LGS (2026 verisi geldi, 3155 lise), Yearly YKS, TUS/DUS, KPSS.
- **KPSS veri kaybı onarıldı:** `kpss_placements.json` 27 Tem'de bot commit'iyle
  1 MB → `[]` olmuştu. Veri geri yüklendi (3188 kayıt) + `_guard.py` yazıldı.
- `_guard.py` kalan 9 scraper'a yayıldı; `transform_yokatlas` sessiz `return`'ü
  ve `yokatlas_scraper`'ın ara-kayıt ezmesi giderildi.
- **ÖSYM yeni URL şeması çözüldü** (`_osym.py`): chunked-hang toleranslı indirme
  (240 sn timeout → 1.0 sn) + `/Duyurular/Index` keşfi. KPSS 2026/1, TUS ve DUS
  2026 verileri geldi.
- **CI kör noktası kapatıldı:** GITHUB_TOKEN push'ları workflow tetiklemiyor →
  CI 07-20'den 09-04'e hiç koşmadı. Haftalık `schedule` eklendi.
- **Ruff `<0.16` sınırı kaldırıldı:** 89 otomatik + 16 elle düzeltme, kalan 80
  için gerekçeli `ignore` (B008 FastAPI, SIM115, BLE001/S110/S112, DTZ011).
- `il_to_bolge` yazım farklarına ve **birleşik konum metnine** dayanıklı hale
  getirildi + `il_ilce_ayikla()`. Bölge çözülen kayıt **147 → 460** (486'da).

**Kariyer planlaması (opencode için)**
- `.beyin/PLAN_KARIYER_YOL_HARITASI.md` — 27 görev, 6 faz, her birinde
  doğrulanabilir "bitti" kriteri. Faz sırası bağımlılık mantığına göre
  düzeltildi: **değer (API+frontend) önce → emniyet → kaynaklar**.
- `.beyin/KAYNAK_HARITASI.md` — 81 il kapsamı keşfi, 3 tur tamamlandı.
- `scripts/opencode-loop.ps1` — opencode'u görevler bitene kadar koşturan
  döngü (tıkanma tespitli).

### Keşif sonuçları (KAYNAK_HARITASI.md'de ayrıntılı)

| Bulgu | Sonuç |
|---|---|
| Kurum-kurum gitmek | ❌ Ortak URL deseni yok; üniversite siteleri soft-404 veriyor |
| **Toplayıcı-önce** | ✅ BİK mevzuatı: kamu kurumları ilanı `ilan.gov.tr`'de yayımlamakla yükümlü, 81 il tek merkezden |
| Kariyer Kapısı | ✅ **`/RSS` açık, 33 ilan, giriş yok** — ilk adaptör bu olmalı |
| ilan.gov.tr API | 🟡 şema + `cityCounts` doğrulandı, oturum şartı çözülmedi |
| Akademik + sağlık | ✅ BİK kategori `73`/`8`'de — ayrı adaptör gereksiz |
| OSB haritası | ✅ 418 OSB, **302 faal, 78/81 il**; ama satırlarda link yok |
| LinkedIn | ❌ `robots.txt` tüm siteyi yasaklıyor (`anthropic-ai` dahil) — KAPALI |
| İŞKUR | ❌ WAF; ilan toplayıcılarda görünüyor, başvuru oraya yönlendirilir |
| Kurum RSS'leri | ❌ 5 kurumda arandı, hepsi yanlış pozitif (soft-404 / HTML) |
| Odalar (ITO/İZTO/ATO) | ❌ iş ilanı kaynağı değil |

## Sıradaki adım
`KAYNAK_HARITASI.md` §8 sonundaki keşif turları: (a) TOBB/odalar firma
kayıt sistemi üzerinden **şirket evreni** çıkarılabilir mi, (b) en yoğun
8-10 ildeki OSB sitelerinde ilan sayfası örneklemi, (c) Vizyoner Genç ve
TÜBİTAK SPA'larının JSON API'si.

## Engeller
- **ilan.gov.tr oturum şartı** — en büyük tek bilinmeyen. Şema hazır ama istek
  kabul edilmiyor. Tarif: başarılı isteğin tam başlıklarını "Copy as cURL" ile
  al, Python'da tekrarla.
- **Repo 230 MB** (F5.3). `chunks.json` 28 MB, her index üretiminde commit;
  `kariyer_ilanlar.json` günlük. Karar bekliyor: HF dataset / delta / ayrı repo.
- **Careerjet tarihleri bozuk** (178/488) — `kariyer_scraper.py:288` RFC-822'ye
  `[:10]` uyguluyor. opencode'un dosyası, ona bırakıldı.
- `unisense.site` + `www.unisense.site` DNS'te çözülmüyor (Vercel'in "2
  misconfigured domain" uyarısı). Kullanıcının registrar hesabında.
- SIM115 (35) ve DTZ011 (5) bilinçli ertelendi — ürün/kapsam kararı ister.

## Dersler (tekrarlanmasın)
- **Eşzamanlı ajanla aynı dosyaya dokunma.** `schemas.py`'de eski bir klondan
  içerik yazıp opencode'un 12 satırlık DTO eklemesini sildim; `f9acddb` ile geri
  alındı. İçeriği HEAD'den değil GÜNCEL uzaktan al.
- **`.ruff_cache` bayat kalabiliyor** — lint'i cache temizleyerek doğrula, yoksa
  yerelde geçip CI'da düşer (bir kez oldu).
- **HTTP 200'e güvenme.** Uydurma bir yol iste; soft-404 veren siteler var.

## Dokunma
- `backend/data/` — pipeline üretir.
- `kariyer_scraper.py`, `kariyer_service.py`, `Kariyer.jsx`, `test_kariyer.py`,
  `schemas.py` — opencode'un aktif alanı.
