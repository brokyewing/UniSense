# Devir — UniSense
**Son araç:** opencode
**Tarih:** 2026-10-24 17:45
**Durum:** aktif

## Nerede kaldık
- **Ponytail refactoring tamamlandı** (208 test yeşil, frontend build başarılı)
- **Founder validation BAŞLADI** — Board simülasyonu tamamlandı:
  - `founder/idea.md` + `founder/board/brief.md` yazıldı
  - 3 lens memo: Offers (7/10, FUND IF), Monopoly (6/10, FUND IF), Product (8/10, FUND)
  - Board özeti: 2 FUND IF + 1 FUND = **FUND IF** (ortalama 7.0/10)
  - Birleştirilmiş 9 koşul checklist'i `founder/board.md`'de

## Sıradaki adım
**`founder-competitors`** → Rakip haritası (yokatlas, özel tercih robotları, danışmanlık firmaları, kariyer siteleri) + boşluk analizi.
Sonra **`founder-consumer`** → 100 simüle alıcı paneli (YKS/DGS/KPSS/LGS/TUS segmentleri).

## Engeller
- Kullanıcı kararı bekleyen: depo boyutu (230 MB), DTZ011 saat dilimi, SIM115 (35 site).
- 87 kayıtta il yok; 58'si konum boş, 28'i "Türkiye" (ülke düzeyi, meşru). Kaynakta yok — çözülemez.
- 4 kariyer testi hâlâ kırmızı (önceden var, bu oturumla alakasız)

## Dokunma
`backend/pyproject.toml` (TRY004 ignore kaldırıldı, commit edilmedi),
`kariyer_service.py` `_KAYNAKLAR` (opencode alanı).