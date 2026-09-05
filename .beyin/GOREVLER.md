# Görevler — UniSense

Durum: `[ ]` açık · `[~]` devam ediyor · `[x]` bitti · `[!]` engellendi

## Açık
- [ ] SIM115 (35 nokta): `json.load(open(p))` → context manager. Şu an ruff'ta
      `ignore`'da, gerekçesi pyproject'te yazılı. Servis kodunda geniş yeniden yazım.
- [ ] DTZ011 (5 nokta): `date.today()` → Europe/Istanbul mı UTC mi? Ürün kararı.

## Kariyer platformu — YOL HARİTASI (ekleyen: Claude Code, 2026-09-05)

**Uygulama sırası ve "bitti" tanımları: `.beyin/PLAN_KARIYER_YOL_HARITASI.md`.**
opencode bu dosyayı sırayla uygular; onay beklemez (kararlar §4'te önceden verildi),
tıkanan kaynakta durmaz (§3 erişim karar ağacı + `[!]` işaretle-geç kuralı).

Hazır keşifler (tekrar araştırma yapılmayacak, §3.1):
- ilan.gov.tr → kimlik doğrulamasız JSON API bulundu (25.062 ilan + şehir kırılımı)
- İŞKUR → WAF teyitli, doğrudan erişim yok; resmî ayna/toplayıcı yolu izlenecek
- ÖSYM → `_osym.py` (toleranslı indirme + Duyurular keşfi) hazır, yeniden kullanılacak

Faz başlıkları: F0 temel şema/bölge/çalışma-şekli/kaynak defteri · F1 kamu hattı ·
F2 özel sektör · F3 API+filtreler · F4 frontend · F5 dayanıklılık.

## Kariyer — canlı veride bulunan iki hata (Claude Code, 2026-09-05 ölçtü)

Canlı API yanıtı incelenerek bulundu, ikisi de gerçek kullanıcıyı etkiliyor:

- [ ] **Careerjet tarihleri bozuk — 178/488 kayıt (%36).**
      `kariyer_scraper.py:267` → `"tarih": (job.get("date") or bugun)[:10]`.
      Careerjet RFC-822 veriyor ("Wed, 29 Jun 2026 ..."), `[:10]` onu
      **"Wed, 29 Ju"** yapıyor. Sıralama ve "bugün yeni" rozeti bununla çalışmaz.
      Jooble'ın `updated` alanı ISO olduğu için satır 245 sorunsuz.
      *Çözüm:* `email.utils.parsedate_to_datetime()` ile ayrıştırıp ISO'ya çevir;
      ayrıştırılamazsa `bugun`. **Bu dosya opencode'da açık, düzeltmeyi o yapsın.**

- [x] **Konum alanı bölge filtresini kırıyordu — 339/486 kayıt (%70).** ÇÖZÜLDÜ.
      `sehir` tek alanda ve kaynaklar arasında TERS SIRADA geliyor:
      Jooble "Ankara, Çankaya" (il, ilçe) — Careerjet "Konak, İzmir" (ilçe, il).
      `il_to_bolge` birleşik metni çözemiyordu → 486 kayıttan yalnız 147'si.
      `domain/geo.py`'ye `il_ilce_ayikla(konum) -> (il, ilce, bolge)` eklendi:
      sıraya güvenmez, hangi parçanın 81 ilden biri olduğuna bakar; "İstanbul
      Avrupa" gibi yaka etiketlerini de kelime bazlı yakalar. **147 → 460.**
      *opencode'a düşen:* normalize fonksiyonlarında `sehir` yerine bu çağrılsın,
      `il`/`ilce`/`bolge` alanları buradan doldurulsun (şema v2, F0.1/F0.2).

## Kaynak rehberi — düzeltme + yeni girdiler (Claude Code, 2026-09-05)

Hazır teslim: **`.beyin/KAYNAK_REHBERI_ONERILERI.md`** — hepsi canlı doğrulandı,
rehberin kendi JSON biçiminde yazıldı. `_KAYNAKLAR` opencode'un alanı, dokunmadım.

- [ ] 🚨 **`kodilan` girdisini SİL** — alan adı el değiştirmiş, ana sayfa
      "Download & Play BDG Game/BDG Win to Earn Real Money". İş arayanı kumar
      sitesine yönlendiriyoruz.
- [ ] `kariyer-kapisi` notu yanlış: "e-Devlet girişi gerekir" — liste için
      GEREKMİYOR (e-Devlet yalnız başvuruda). RSS de eklensin.
- [ ] `ilan-gov-tr` notu yanlış: "Botlara API kapalı" — API açık ve
      kimlik doğrulamasız.
- [ ] `ilan-yok` girdisi geçersiz (adres hiç çözülmüyor) → AkademikAğ ile değiştir.
- [ ] `vizyoner-genc` → `savunmakariyer.com` olarak güncellenmeli (site taşındı).
- [ ] `kamu-sosyal` (LinkedIn) kalsın ama nota "UniSense bu kaynaktan çekmez,
      robots taramaya kapalı" eklensin.
- [ ] 9 yeni girdi eklensin (Savunma Kariyer, ilan.gov.tr Akademik, AkademikAğ,
      isbul.net, ATS panoları, Wellfound/RemoteOK/Bionluk, OSBÜK, TOBB Sanayi).
      Rehber 42 → 50 kaynak.

## Bitti
- [x] Ruff bulguları temizlendi, `<0.16` üst sınırı kaldırıldı (bb9bc50)
- [x] TUS/DUS + KPSS Data Sync gerçek Actions koşusunda YEŞİL (dispatch, 2026-09-04)
- [x] Boş-sonuç bekçisi kalan 9 scraper'a yayıldı (d1bfa23)
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

## Plan — Kariyer bölüm seçici (ekleyen + uygulayan: opencode, 2026-09-05 02:15)
- [x] Geniş çekim: Jooble 4 sorgu×5 sayfa + Careerjet 3 sorgu×3 sayfa (bölüm-agnostik)
- [x] Çift taraflı etiket: 12 bölüm, başlık+açıklama fold eşleşme (`bolumler: [...]`)
- [x] 30 günlük kayan pencere budaması (`_merge`); canlı koşu: 563 çekim → 76 budama → 488 kayıt
- [x] API: `?bolum=` filtresi + `/kariyer/bolumler` (sayımlı taksonomi)
- [x] Frontend: üstte bölüm seçici chips + kartlarda bölüm rozetleri
- [x] Doğrulama: pytest 21/21, ruff temiz, API 200, build 631 URL; push 806961f

## Plan — Kariyer kaynak envanteri (ekleyen: opencode, 2026-09-04 22:58)
- [x] Hat A kamu kaynakları (A1–A18 + 12 ek, 30 kamu toplam) scraper önceliğine bağlandı
- [x] Hat B career-ops TR sorguları referans alındı + CANLI adaptör yazıldı (Jooble+Careerjet, 0947055)
- [x] API anahtarları girildi (career-ops .env) + canlı doğrulama: careerjet 117 + jooble 80 + RG 1 = 198 kayıt (54c1a9b)
- [ ] Anahtarlar UniSense'e taşınmalı: backend/.env (yerel) + GitHub Secrets (CI); şimdilik career-ops .env'den okunuyor
- [ ] Jooble detay linkleri botlara 403 (WAF) — kullanıcı tarayıcısında açılır; sorun değil ama not düşüldü
- [ ] Kapalı TR şirket URL'leri doğrulanmalı (Getir, Baykar, Roketsan, STM, Papara...; career-ops tarafı)
- [x] `kaynak_hat: kamu|ozel` alanı + API `hat` filtresi uygulandı
- Detay: `.beyin/PLAN_KARIYER.md` Ek bölümü (21 sayfalık PDF metni + portals.yml satır referanslı)
