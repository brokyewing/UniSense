# Devir — UniSense
**Son araç:** Claude Code
**Tarih:** 2026-09-06 00:30
**Durum:** bekliyor

## Nerede kaldık
- Kullanıcının bildirdiği üç sorun kapatıldı (commit `83f0e4a`):
  `unisense.site` `render.yaml` CORS + `frontend/vercel.json` yönlendirmelerinden
  silindi; `geo.py`'ye ilçe→il indeksi (98 tekil ilçe, belirsizler hariç);
  `kariyer_scraper.py` çalışma şekli çıkarımı + `detay.calisma_sekli_kaynak`.
- Ölçüm (1935 kayıt): çalışma şekli 27 → 568 (%1,4 → %29,4). Dağılım:
  281 kamu varsayımı, 260 dolaylı sinyal, 27 kaynak alanı. **Yalnız 27'si
  gerçekten güvenilir** — arayüz bunu ayırt etmeli (GOREVLER'de görev açıldı).
- ruff temiz, 284 test yeşil (20 yeni test: ilçe çözümü + çalışma şekli).
- `backend/pyproject.toml`'deki TRY004 ignore silinmesi **commit edilmedi** —
  başka bir aracın çalışma kopyası olabilir; lint onsuz da temiz.

## Sıradaki adım
opencode: `Kariyer.jsx`'te `calisma_sekli_kaynak` rozetlerini uygula
(`varsayim`/`dolayli` "tahmini" diye gösterilsin), sonra yol haritası F1
(API filtreleri + UI) ile devam.

## Engeller
- Kullanıcı kararı bekleyen: depo boyutu (230 MB, `chunks.json` her indeks
  yeniden kurulumunda 28 MB), DTZ011 saat dilimi, SIM115 (35 site).
- 87 kayıtta il yok; 58'inde konum alanı tamamen boş, 28'i "Türkiye"
  (ülke düzeyi, meşru). Kaynakta yok — çözülemez.

## Dokunma
`backend/pyproject.toml` (sahipsiz yerel değişiklik var),
`kariyer_service.py` `_KAYNAKLAR` (opencode'un alanı).
