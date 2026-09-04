# Görevler — UniSense

Durum: `[ ]` açık · `[~]` devam ediyor · `[x]` bitti · `[!]` engellendi

## Açık
- [ ] TUS/DUS + KPSS Data Sync gerçek Actions koşusunda doğrulanmalı (dispatch)
- [ ] `_guard.py` diğer scraper'lara da uygulanmalı (urap, wikipedia_*, dgs, iskur, ...)
- [ ] 149 ruff bulgusu temizlenip `<0.16` üst sınırı kaldırılmalı

## Bitti
- [x] CI kör noktası kapatıldı — haftalık schedule (4ebdd61)
- [x] yearly-data-sync zinciri gerçek koşuda doğrulandı (dispatch, 2026-09-04)
- [x] LGS 2026 verisi repo'ya girdi — yil=2026, 3155 kayıt (fbad2cc)
- [x] ÖSYM yeni URL şeması çözüldü, KPSS/TUS/DUS scraper'ları çalışıyor (96aed46)
- [x] lgs-sync / tusdus-sync / yearly-data-sync onarildi (a25d823)
- [x] KPSS verisi geri yuklendi + bekci eklendi (e849f23)
- [x] CI yesile alindi (0597d93)

## Plan — Responsive 1. Adım (ekleyen: opencode, 2026-09-04 22:41; uygulayan: opencode, 2026-09-04 23:07)
- [x] App shell full-width: `App.jsx` max-w-6xl kaldır, simetrik padding (px-4 → md:px-6 → xl:px-8 → 3xl:px-12)
- [x] tailwind breakpoint ekle: `xs: 360px` + `3xl: 1920px`
- [x] Grid revizyonu önce: Home / Compare / Hesap / Pusula (3xl'de 4 sütun)
- [x] Sabit çok sütunlular incelendi: Pusula grid-cols-5 (puan skalası) + Hesap grid-cols-3/5 (sekme) bilinçli sabit, mobilde sığıyor — değiştirilmedi
- [x] İç içe max-w-3xl/4xl daraltmalarını temizle (Login hariç — 20 sayfa kökü + Search -mx hack)
- [x] Doğrulama: `npm run build` temiz (vite 33sn + prerender 630 URL); ekran matriksi kullanıcıya kaldı
- Detay: `.beyin/PLAN_RESPONSIVE_1ADIM.md` (uygulandı 23:07; `npm run build` temiz)

## Plan — Kariyer Sekmesi (ekleyen: opencode, 2026-09-04 22:50; uygulayan: opencode, 2026-09-05 00:46)
- [x] Kaynak araştırması + kararı: Hat A (18 kamu) + Hat B (career-ops TR); ilan.gov.tr API + kamuilan postback + İŞKUR WAF + Kariyer Kapısı login bulguları PLAN'da
- [x] Backend scraper: `kariyer_scraper.py` (RG günlük sayı + sinyal) + `rg_chain.pem` zincir + guard; ilk koşu yerelde yeşil (25 PDF, 234 sayfa)
- [x] API: `GET /api/v1/kariyer/{ilanlar,kaynaklar,meta}` (mevcut path'lere dokunmadan; 4 istek 200)
- [x] Günlük cron: `kariyer-sync.yml` (05:00 UTC + dispatch + bekçi); ilk CI koşusu bekleniyor
- [x] Frontend: nav Kariyer + `/kariyer` route + `Kariyer.jsx` + SEO + prerender (631 URL)
- [x] Doğrulama: pytest 10/10 (kariyer) + 92 toplam, ruff temiz, vite+prerender temiz
- Detay: `.beyin/PLAN_KARIYER.md` (uygulandı; Hat B site-sorgu fazı sonraki iş)

## Plan — Kariyer kaynak envanteri (ekleyen: opencode, 2026-09-04 22:58)
- [ ] Hat A kamu kaynakları (A1–A18) scraper önceliğine bağlanmalı (önce A1/A9/A5)
- [ ] Hat B career-ops TR sorguları referans alınmalı (kariyer.net, secretcv, techcareer, careerjet tr_TR...)
- [ ] Kapalı TR şirket URL'leri doğrulanmalı (Getir, Baykar, Roketsan, STM, Papara...)
- [ ] `kaynak_hat: kamu|ozel` alanı + API `hat` filtresi taslakta; kodlamada uygulanacak
- Detay: `.beyin/PLAN_KARIYER.md` Ek bölümü (21 sayfalık PDF metni + portals.yml satır referanslı)
