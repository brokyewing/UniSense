# Devir — UniSense
**Son araç:** Claude Code
**Tarih:** 2026-09-05 04:30
**Durum:** bekliyor

## Nerede kaldık
Sekiz commit push edildi, **CI yeşil** (96aed46 doğrulandı).

- `583d5c8` keep-alive: GitHub cron ölçüldü (istenen 10 dk, gerçek 108-273 dk).
  Her tetiklenme 5 dk arayla 12 ping atıyor. Asıl çözüm cron-job.org'daki 5 dk'lık
  harici ping — kullanıcı kurdu (timeout 120 sn).
- `a25d823` üç sync workflow onarımı: lgs-sync + tusdus-sync `unisense` paketini
  kurmuyordu; yearly-data-sync'te `yokatlas-py` beyan edilmemişti (`[scrape]`
  extra'sı) ve `yokatlas_extra_scraper` zorunlu `--target` olmadan çağrılıyordu.
- `b09e279` ruff `<0.16` sabitlendi (0.15.4 temiz / 0.16.6 → 149 bulgu).
- `e849f23` KPSS veri kaybı onarıldı + `scrapers/_guard.py` (boş veya %50'den
  fazla küçülen sonuç dosyaya yazılmaz, exit 1).
- `0597d93` CI `pip install pytest ruff` diyerek pyproject pinlerini atlıyordu →
  `pip install -e ".[dev]"`. CI yeşile döndü.
- `755018a` tusdus artık hiç veri üretemezse exit 1 (sessiz yeşil yoktu).
- `96aed46` **ÖSYM yeni URL şemasına geçildi — scraper'lar yeniden çalışıyor.**
- `9968d5d` .beyin + orkestra dosyaları repoya alındı.
- `4ebdd61` CI'a haftalık `schedule` + `workflow_dispatch` eklendi. GITHUB_TOKEN
  ile atılan bot push'ları workflow tetiklemiyor (GitHub'ın sonsuz döngü
  koruması); CI 07-20'den 09-04'e hiç koşmadı, ruff kayması ve KPSS veri kaybı
  bu kör noktada 6 hafta gizli kaldı. Haftalık koşu ikisini de yakalardı.

### ÖSYM çözümü (96aed46) — beş kırılma
1. www.osym.gov.tr `chunked` gönderiyor ama SONLANDIRICI CHUNK'I HİÇ
   GÖNDERMİYOR. İçerik tam geliyor (~775 KB), bağlantı kapanmıyor;
   `requests.get().text` read timeout'a düşüp gövdeyi çöpe atıyordu.
   Yeni `_osym.fetch_tolerant()` akıtarak biriktiriyor → /Duyurular/Index
   583 KB, **1.0 saniye** (önceden 240 sn timeout).
2. URL şeması slug-only oldu; eski `/TR,NNNNN/...html` 404.
3. Eski arama endpoint'i ana sayfaya 302 → keşif `/Duyurular/Index`'e taşındı.
4. KPSS'in yeni PDF adlarında `minmax` yok, `en-kucuk-ve-en-buyuk` var.
5. `LEVEL_HINTS` (`lisans`/`onl`) yeni adlardaki `lsans`/`on-lsans` ile
   eşleşmiyordu. Slug'lar tutarsız (kpss20252 / kpss-20261, 2026dus-1donem /
   2025tus-2-donem) → **URL üretilemez, keşfedilmeli.**

Ayrıca kpss_scraper'a arşiv birleştirme eklendi (lgs_scraper deseni): ÖSYM eski
duyuruları kaldırdığı için 2025/1 keşfedilemiyor; bu koşuda üretilmeyen dönemler
mevcut dosyadan taşınıyor. İlk denemede tam bu yüzden 3188→2913 düşmüştü.

Sonuç (canlı): kpss_placements 3188 → **4293** (2026/1 eklendi, 2025/1+2025/2
korundu); tus_rankings 2025 1.Dönem → **2026 1.Dönem** (2895 program);
dus_rankings 2025 2.Dönem → **2026 1.Dönem** (424 program).
build_chunks bu dosyaları okumuyor → RAG index'i etkilenmez.
ruff temiz, pytest **123 passed** (önceden 111).

### Bekçi yayılımı (d1bfa23)
`_guard.py`'ye `check()` eklendi (yazmadan ÖNCE doğrular, yazmayı çağırana
bırakır) ve kalan 9 scraper'a uygulandı: urap, wikipedia_uni,
wikipedia_infobox, dgs, iskur_mbk, avesis, transform_yokatlas, kpss_kilavuz,
yokatlas. Her girişe ScrapeGuardError → exit 1 sarmalı eklendi.
İki özel durum:
- transform_yokatlas RAW yoksa sessizce `return` ediyordu (adım YEŞİL kalıyordu)
  → artık hata fırlatıyor. Dört çıktı yazılmadan önce topluca doğrulanıyor;
  biri şüpheliyse hiçbiri yazılmıyor.
- yokatlas_scraper'ın döngü içi "Ara kayıt"ı her turda ASIL dosyayı eziyordu
  (ilk tur ~5.7k program ile 12.2k'lık dosyayı). Artık
  `programs_2025.partial.json`'a yazıyor; asıl dosya döngü bitince bekçiden
  geçerek tek seferde yazılıyor. .gitignore'a `*.partial.json` eklendi.
Doğrulandı: check() sınır testi (boş/30/49/50/80/150/force/yeni-dosya),
transform_yokatlas boş raw ile ENGELLENDİ ve mevcut 228 kayıt KORUNDU,
temiz klonda ruff temiz + pytest 127 passed.

### Lint sözleşmesi (bb9bc50, f9acddb)
`<0.16` üst sınırı KALDIRILDI; en son ruff (0.16.6) ile tüm repo temiz.
89 bulgu otomatik, 16 bulgu elle düzeltildi (hiçbiri davranış değiştirmeden).
Kalan 80 için `ignore` listesi gerekçeleriyle pyproject'te: B008 (FastAPI
Depends — extend-immutable-calls ile çözüldü), SIM115 (35), BLE001/S110/S112
(bilinçli dayanıklılık), DTZ011 (timezone ürün kararı).
`select` bilinçli YAZILMADI: aile bazında seçmek varsayılanda olmayan
kuralları da açıyor — RUF001/002/003 tek başına 3774 bulgu üretti (Türkçe
karakterleri "belirsiz" sayıyor). Varsayılan set sürümle değişebilir; haftalık
CI cron'u (4ebdd61) bunu bir hafta içinde görünür kılar.

**Bu iş sırasında bir hata yapıldı ve düzeltildi:** f2d2dde'de schemas.py'nin
lint düzeltmesi eski bir klonda hesaplandı; arada opencode 806961f ile aynı
dosyaya Kariyer DTO'ları eklemişti ve eski içerik yazılınca bunlar silindi
(636→624 satır). f9acddb ile aynen geri getirildi. Ders: eşzamanlı ajan
varken dosya içeriğini HEAD'den değil, GÜNCEL uzaktan almak gerekiyor.

## Sıradaki adım
Açık iş kalmadı. GOREVLER.md'deki iki madde (SIM115 yeniden yazımı, DTZ011
timezone kararı) bilinçli olarak ertelendi; ikisi de ürün/kapsam kararı ister.

## Engeller
- (ÇÖZÜLDÜ) Dört sync workflow'u da dispatch ile YEŞİL koştu: LGS, Yearly YKS,
  TUS/DUS, KPSS. Veri commit'leri:
  lgs_liseler.json yil=2026 / 3155 kayıt (fbad2cc), YKS chunks.json yeniden
  üretildi (4fea0c1), RAG Index Sync de yeşil.
- Diğer scraper'larda (urap, wikipedia_*, dgs, iskur, avesis,
  transform_yokatlas, kpss_kilavuz, yokatlas_scraper) boş-sonuç bekçisi yok;
  `_guard.py` oraya da uygulanmalı.
- Vercel: "2 misconfigured domains" + "failed production deployment"
  e-postaları incelenmedi.

## Dokunma
- `backend/data/` — normalde pipeline üretir. 96aed46'da bilinçli olarak elle
  commit'lendi (build_chunks okumadığı için index'i bozmuyor).
- opencode aynı repoda "Kariyer" özelliği üzerinde çalışıyor (0c02d8b, 01:14).
  `GOREVLER.md`'deki Kariyer/Responsive planları onun.
