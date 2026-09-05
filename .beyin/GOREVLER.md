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

## Kapsama — "tek bir site bile kalmasın" (Claude Code, 2026-09-05 ölçtü)

Ölçüm: **7 kaynak fiilen toplanıyor**, rehberde 42 var, **~35'i yalnız link**.
Ayrıntı ve öncelik sırası: **`.beyin/KAPSAMA_MATRISI.md`**

Araştırması BİTMİŞ, sadece adaptör bekleyen ikisi (sıfır araştırma gerekiyor):

- [ ] **savunmakariyer.com adaptörü** — API tamamen çözüldü
      (`KAYNAK_HARITASI` §10). 24 ilan + 343 onaylı firma + 81 il; auth yok;
      `jobLocation`→il, `endDate`→son_basvuru. ASELSAN/HAVELSAN/ROKETSAN/
      STM/BAYKAR/TUSAŞ/TEI bu tek kaynakta.
- [ ] **Lever ATS adaptörü** — 6 slug doğrulandı (§9.3): `trendyol`,
      `peakgames`, `dreamgames`, `getmidas`, `iyzico`, `insiderone`.
      `api.lever.co/v0/postings/<slug>?mode=json`, auth yok, ~101 TR ilanı.
      ⚠️ konum alanı bazı şirketlerde bozuk → `il_to_bolge` ile doğrula.

Sonraki öncelikler: kariyer.net (robots ilan yollarına izin veriyor) →
eleman.net (81 il iddiası) → yenibiris/isbul/secretcv.

## 🚨 Budama hatası — AÇIK ilanlar siliniyor (Claude Code ölçtü, 2026-09-05)

`kariyer_scraper.py` `_merge()` içindeki iki budama kuralından **ikincisi
hatalı**:

```
~1099  # 1) son_basvuru geçmişse (7 gün tolerans) at   -> DOĞRU
~1109  # 2) tarih (YAYIN tarihi) 30 günden eskiyse at  -> HATALI
       ref = k.get("tarih") or k.get("ilk_gorulme")
       if yas > SAKLA_GUN: birlesik.remove(k)
```

İkinci kural, **başvurusu hâlâ açık** ilanları siliyor. Süre kontrolü zaten
1. kuralda `son_basvuru` ile doğru yapılıyor; ikinci kural onu eziyor.

**Ölçülen kayıp (2026-09-05):**

| Kaynak | API/RSS'te | Kaydedilen | Kayıp | Sebep |
|---|---|---|---|---|
| Savunma Kariyer | 24 | **12** | 11 | `startDate` 30 günden eski ama `endDate` gelecekte |
| Kariyer Kapısı | 33 | **30** | 3 | `pubDate` 30 günden eski |

Silinen gerçek örnekler (hepsi **açık**):
- "Kablaj Teknisyeni" — yayın 2026-06-10, **son başvuru 2026-10-10**
- "Beyaz Yakalılar Genel Başvuru" — yayın 2026-02-23, **son başvuru 2027-02-23**
- "Cad-Cam Mühendisi (Kayseri)" — yayın 2026-04-15, **son başvuru 2026-12-15**
- KAMU İHALE KURUMU personel ilanı — yayın 2026-04-20

Toplam **14 açık ilan** kayıp; kaynak eklendikçe büyür. Uzun süre açık kalan
kurumsal ilanlar (genel başvuru havuzları) sistematik olarak eleniyor.

- [x] ~~**Düzeltme:** `son_basvuru` DOLU ve gelecekteyse yaş budamasını ATLA.~~ ÇÖZÜLDÜ (88a6d5b)
      Yaş kuralı yalnız `son_basvuru`'su olmayan kayıtlar için çalışsın.
      *Bitti:* Savunma Kariyer 24 (ACTIVITY hariç 23), Kariyer Kapısı 33 kayıt
      yazılıyor; testte açık-ama-eski bir ilan korunuyor.

## İl bilgisi eksik kayıtlar — yardımcı HAZIR (Claude Code, 2026-09-05)

Denetim: **792 kaydın 128'inde il/bölge YOK** — hepsi kamu kaynağı
(kamuilan.sbb 67, Kariyer Kapısı 30, AkademikTR 30, Resmî Gazete 1).
Bölge filtresi bu kayıtlarda çalışmıyor.

`geo.metinden_il_bul(metin)` yazıldı ve testli (`geo.py` benim alanım):
kurum adından il çıkarıyor, adında il geçmeyenler için istisna tablosu var
(Karadeniz Teknik→Trabzon, ODTÜ→Ankara, Gebze Teknik→Kocaeli,
İnebolu→Kastamonu…). **Ölçüm: 128 kayıttan 82'si (%64) kurtarılıyor.**

- [ ] Adaptörlerde `il` boşsa `metinden_il_bul(kurum)` → olmazsa
      `metinden_il_bul(baslik)` çağrılsın; `bolge` bundan türetilsin.
      *Bitti:* ili boş kayıt 128 → ~46'ya düşüyor.

## ⚠️ CI 4 saat kırmızı kaldı — commit öncesi ruff ZORUNLU

CI 2026-09-05 sabahından beri **18 commit boyunca kırmızıydı** ve kimse fark
etmedi. Sebep birikmiş lint borcu: `kariyer_scraper.py` 17, `test_kariyer.py` 11,
`kariyer_registry.py` 2 hata. `ba1c12f` ile temizlendi.

- [ ] **Her commit öncesi `ruff check src tests --fix` çalıştır.** Yeşil değilse
      commit etme. Kırmızı CI'a alışmak, gerçek hataları görünmez yapıyor —
      bugün Careerjet tarih hatası ve açık-ilan budaması tam bu yüzden günlerce
      fark edilmedi.
- [ ] opencode'un çalışma ağacındaki `kariyer_scraper.py` / `test_kariyer.py`
      kopyaları `ba1c12f`'teki lint düzeltmelerini İÇERMİYOR. Commit'lemeden
      önce `git pull --rebase` yapıp ruff'ı tekrar çalıştır, yoksa düzeltmeler
      geri gider.

### Düzeltilenler (bu oturumda, Claude Code)

- [x] Careerjet tarihleri — RFC-822 ayrıştırma (`88a6d5b`), 228 kayıt
- [x] Açık ilanların budanması — `son_basvuru` varsa yaş kuralı atlanır
      (`88a6d5b`), 14 açık ilan kurtarıldı
- [x] Birikmiş lint borcu (`ba1c12f`)

## Denetim bulguları — veri kalitesi (Claude Code, 2026-09-05)

**1. Jooble `kurum` alanı yanlış — kullanıcı işveren yerine site adı görüyor.**
302 kaydın tamamında `kurum` = kaynak pano (`yenibiris.com` 117,
`elemanonline.com.tr` 62, `bakiciburada.com` 56, `secretcv.com` 31,
`isbul.net` 16…). Kodda not düşülmüş ("Jooble kaynak panoyu verir, işvereni
değil") ama alan yine de `kurum`'a yazılıyor.

- [ ] `kurum` boş bırakılsın, pano adı `detay.kaynak_pano`'ya taşınsın.
      Kartta "yenibiris.com" işveren gibi görünmemeli.

**2. `calisma_sekli` neredeyse tamamen boş — online/yüz yüze filtresi çalışmaz.**
840 kayıttan **832'si `bilinmiyor`** (4 online, 4 yüz yüze). F0.3 kalıp tablosu
yazıldı ama Jooble/Careerjet özetleri çok kısa olduğu için eşleşme çıkmıyor.

- [ ] Çıkarımı ilan **detay sayfasından** yap ya da kaynak alanlarını kullan
      (Lever `workplaceType`, eleman.net JSON-LD `jobLocationType`).
      *Bitti:* `bilinmiyor` oranı %99'dan belirgin şekilde düşüyor.

**3. `istihdam_turu` de %94 boş** (791/840). Savunma Kariyer (`jobType`) ve
Kariyer Kapısı (`category`) dolduruyor; toplayıcılar doldurmuyor.

**4. Careerjet'te 103 kayıtta `kurum` boş** (256 kaydın %40'ı).

## `calisma_sekli` — gerçekçi tavan ÖLÇÜLDÜ (Claude Code, 2026-09-05)

Kullanıcının "online / yüz yüze" filtresi için kaynakların **fiilen ne verdiği**
ölçüldü. Sonuç: bu alan kaynakların çoğunda **yok**, metin çıkarımı da zayıf.

| Kaynak | Kayıt | Çalışma şekli alanı | Doluluk |
|---|---|---|---|
| **Lever ATS** (henüz eklenmedi) | 91 | **`workplaceType`** | **%100** — hibrit 45, yerinde 44, uzaktan 2 |
| Savunma Kariyer | 23 | ✗ yok (`jobType` istihdam türü) | %0 |
| eleman.net | — | `jobLocationType` **hep `None`** | %0 |
| ilan.gov.tr / Kariyer Kapısı / kamuilan | 226 | ✗ yok | %0 |
| Jooble + Careerjet | ~1561 | ✗ yok, özetler çok kısa | ~%0 |

**Bugün: 1843 kayıttan yalnız 17'si dolu (%1).**

Gerçekçi tavan:
- Lever eklenince **+91** (%100 güvenilir)
- Kamu ilanlarına `yuzyuze` **varsayılanı** verilirse **+282** — devlet kadroları
  doğası gereği yerinde; ama bu bir VARSAYIM, veri değil. Kabul edilirse
  `detay.calisma_sekli_kaynak = "varsayim"` diye işaretlenmeli.
- Kalan ~1470 (Jooble/Careerjet) için tek yol **ilan detay sayfasını çekmek** —
  toplayıcı linkleri yönlendirme olduğu için maliyetli.

→ **En iyi ihtimalle ~%21 doluluk.** Filtre bu haliyle ilanların çoğunu
gösteremez.

- [ ] **Ürün kararı gerekiyor:** (a) filtreye "belirtilmemiş" seçeneği ekle ve
      kısmi doluluğu kabul et, (b) kamu için varsayılan ata, (c) detay sayfası
      çekmeyi göze al. Öneri: (a)+(b); (c) maliyeti yüksek.

## Toplanmış ama kullanılmayan veri (Claude Code ölçtü, 2026-09-05)

**1. 🎁 Bedava kazanç: Jooble `detay.tur` → `istihdam_turu`.**
Jooble'ın `type` alanı **744 kayıttan 658'inde dolu (%88)** ve zaten
`detay.tur`'a yazılıyor — ama `istihdam_turu` alanına eşlenmiyor, o yüzden
o alan %94 boş görünüyor.

```
Tam zamanlı 617 | Yarı zamanlı 31 | Staj 6 | Geçici 1 | (boş) 86
```

- [ ] `detay.tur` → `istihdam_turu` eşlemesi ekle
      (`tam zamanlı→tam_zamanli`, `yarı zamanlı→yari_zamanli`, `staj→staj`,
      `geçici→gecici`). **Yeni istek gerekmiyor, veri elde.**
      *Bitti:* `istihdam_turu` doluluğu %6'dan ~%40'a çıkıyor.

**2. `calisma_sekli` metin çıkarımının tavanı: %8.**
1965 kaydın başlık+özetinde tarama: **147 yüz yüze, 7 online/hibrit = 154 (%8)**.
Özetler ortalama 201 karakter — çoğu ilan çalışma şeklini hiç yazmıyor.
Yakalananlar gerçek ("Uzaktan Yazılım Mühendisi", "Home Office Çağrı Merkezi").
⚠️ 147 "yüz yüze" mağaza/şube/fabrika kelimelerinden geliyor — dolaylı sinyal,
`detay.calisma_sekli_kaynak="metin"` diye işaretlenmeli.

**3. Careerjet'te iki ölü alan.**
`detay.maas` **0/929**, `detay.site` **0/929** — API bu alanları hiç
döndürmüyor. Kod doğru okuyor, veri yok.

- [ ] Ya alanları kaldır ya da Careerjet API çağrısına eksik parametre var mı
      diye bak (dokümanda `site` alanı vaat ediliyor).

## 🚨 Lint düzeltmeleri İKİNCİ KEZ geri gitti — kurulum gerekiyor

`ba1c12f`'te düzelttiğim lint hataları (RUF059 `g3`, RUF012 `ORNEK_AD`, B023
closure, I001) opencode kendi çalışma kopyasını commit'leyince **aynen geri
geldi**. `df00c49`'da 34 hata olarak tekrar ölçüldü ve yeniden düzeltildi.

- [ ] **`scripts/pre-commit.sh` kancasını kur** (her araç kendi tarafında):
      ```
      git config core.hooksPath scripts/githooks
      mkdir -p scripts/githooks && cp scripts/pre-commit.sh scripts/githooks/pre-commit
      chmod +x scripts/githooks/pre-commit
      ```
      Commit öncesi ruff + pytest çalıştırır; kırıksa commit'i durdurur.
      Zorunlu hallerde `git commit --no-verify`.

- [ ] **`robots_kontrol` eksik — CI kırık.** `tests/test_kariyer.py`
      `kariyer_registry`'den `robots_kontrol` import ediyor ama fonksiyon yok:
      `ImportError: cannot import name 'robots_kontrol'`. Test, uygulamasından
      önce commit'lenmiş. **Bu opencode'un yarım özelliği**, dokunmadım —
      fonksiyon eklenene kadar CI kırmızı kalır.

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

## Kariyer — çalışma şekli görüntüleme (ekleyen: Claude Code, 2026-09-06)
Backend artık `detay.calisma_sekli_kaynak` yazıyor: `beyan` | `dolayli` |
`varsayim` | `kaynak`. Ölçüm (1935 kayıt): 568 kayıtta çalışma şekli var ama
bunun **281'i kamu varsayımı, 260'ı dolaylı sinyal** — yani yalnız 27'si
gerçekten güvenilir.

- [ ] `Kariyer.jsx`: `varsayim` ve `dolayli` rozetleri soluk/işaretli göster
      (ör. "Yüz yüze (tahmini)"); `beyan`/`kaynak` normal.
- [ ] Çalışma şekli filtresi `varsayim` kayıtları varsayılan olarak dahil
      etsin ama "yalnız doğrulanmış" seçeneği bulunsun.
- Kaynak: `kariyer_scraper.py` `_calisma_sekli_kaynak` (satır ~365).

