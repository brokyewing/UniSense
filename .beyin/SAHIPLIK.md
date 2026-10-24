# Dosya Sahipliği — eşzamanlı ajan çakışmasını önleme

**Neden var:** 2026-09-05'te Claude Code ve opencode aynı repoda eşzamanlı
çalışırken `schemas.py`'de çakışma oldu; Claude Code eski bir klondan içerik
yazınca opencode'un yeni eklediği 12 satırlık DTO **silindi** (`f9acddb` ile geri
alındı). Bu dosya aynı hatanın tekrarını engeller.

---

## 1. Kural — üç adım, istisnasız

**Bir dosyaya yazmadan önce:**

1. `git status --porcelain <dosya>` — çıktı varsa **başkası üzerinde çalışıyor**,
   sen dokunma.
2. `git log --oneline -1 <dosya>` — son commit son 30 dakikadaysa aynı şey
   geçerli.
3. İçeriği **HEAD'den değil, `git fetch` sonrası `origin/main`'den** al. Eski bir
   klondan/kopyadan içerik yazmak yukarıdaki veri kaybının sebebiydi.

**Yazdıktan sonra:** kendi dosyalarını commit et, başkasınınkini stage'leme.
`git add .` KULLANMA — dosyaları tek tek ekle.

---

## 2. Alan paylaşımı

Aşağıdaki bölünme, iki aracın birbirine değmeden ilerlemesi içindir.

### opencode'un alanı (Claude Code dokunmaz)

- `backend/src/unisense/infrastructure/scrapers/kariyer_scraper.py`
- `backend/src/unisense/infrastructure/scrapers/kariyer/` (adaptörler)
- `backend/src/unisense/application/services/kariyer_service.py`
- `backend/src/unisense/api/v1/schemas.py`, `routes.py` (Kariyer uçları)
- `backend/tests/test_kariyer.py`
- `frontend/src/pages/Kariyer.jsx`
- `backend/data/kaynaklar/is_kaynaklari.yml`

### Claude Code'un alanı (opencode dokunmaz)

- `backend/src/unisense/domain/geo.py` + `tests/test_geo_bolge.py`
- `backend/src/unisense/infrastructure/scrapers/_guard.py`, `_osym.py`
- `.github/workflows/*` (CI, keep-alive, sync workflow'ları)
- `backend/pyproject.toml` (lint/bağımlılık sözleşmesi)
- `scripts/opencode-loop.ps1`

### Ortak alan — sıraya girerek

- `.beyin/*` — **append-only davran.** `GUNLUK.md`'ye satır ekle, silme.
  `GOREVLER.md`/plan dosyalarında **yalnız kendi bölümünü** düzenle.
- `README.md`, `AGENTS.md`

---

## 3. Bir dosyayı devralmak gerekirse

Karşı tarafın alanındaki bir şeyi düzeltmen gerekiyorsa **düzeltme, bildir:**

1. `GOREVLER.md`'ye görev yaz: dosya + **satır numarası** + sorun + önerilen çözüm.
2. Sahibi düzeltir.

Örnek (işe yaradı): Careerjet tarih hatası `kariyer_scraper.py:288` olarak
yazıldı, Claude Code dosyaya dokunmadı.

**İstisna:** düzeltme karşı tarafın dosyasına dokunmadan yapılabiliyorsa onu
tercih et. Örnek: `il_to_bolge` birleşik konum metnini çözemiyordu; çağıran
`kariyer_scraper.py` (opencode'un dosyası) yerine `geo.py`'nin kendisi
toleranslı yapıldı — tek satır çakışma olmadan 147→460 kayıt düzeldi.

---

## 4. Hızlı kontrol komutu

```bash
git fetch -q origin && git status --porcelain && git log --oneline -3
```

Çıktıda senin alanın dışında değişiklik varsa: bekle veya başka göreve geç.
