# Devir — UniSense
**Son araç:** Claude Code
**Tarih:** 2026-09-05 02:20
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

## Sıradaki adım
Actions'tan "TUS/DUS Data Sync" ve "KPSS Data Sync"i workflow_dispatch ile
tetikle — ÖSYM düzeltmesinin (96aed46) gerçek Actions ortamında da çalıştığını
doğrulamak için. Sonra `_guard.py` diğer 8 scraper'a uygulanacak.

## Engeller
- TUS/DUS ve KPSS Data Sync henüz gerçek Actions koşusunda denenmedi
  (workflow_dispatch token gerektiriyor, kullanıcı tetiklemeli). LGS ve
  Yearly YKS 2026-09-04'te dispatch ile YEŞİL koştu ve veriyi commit'ledi:
  lgs_liseler.json yil=2026 / 3155 kayıt (fbad2cc), YKS chunks.json yeniden
  üretildi (4fea0c1), RAG Index Sync de yeşil.
- Diğer scraper'larda (urap, wikipedia_*, dgs, iskur, avesis,
  transform_yokatlas, kpss_kilavuz, yokatlas_scraper) boş-sonuç bekçisi yok;
  `_guard.py` oraya da uygulanmalı.
- 149 ruff bulgusu temizlenmeden `<0.16` üst sınırı kaldırılmamalı.
- Vercel: "2 misconfigured domains" + "failed production deployment"
  e-postaları incelenmedi.

## Dokunma
- `backend/data/` — normalde pipeline üretir. 96aed46'da bilinçli olarak elle
  commit'lendi (build_chunks okumadığı için index'i bozmuyor).
- opencode aynı repoda "Kariyer" özelliği üzerinde çalışıyor (0c02d8b, 01:14).
  `GOREVLER.md`'deki Kariyer/Responsive planları onun.
