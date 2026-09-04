# Kariyer Yol Haritası — Türkiye İş İlanları Platformu

**Yazan:** Claude Code · **Tarih:** 2026-09-05
**Kime:** opencode (uygulayan) · **Statü:** yürürlükte, sırayla uygulanır

> **Amaç:** Kariyer.net / Indeed tarzı bir iş ilanı platformu. Kamu (KPSS'li +
> KPSS'siz) ve özel sektör, Türkiye'de faaliyet gösteren tüm kaynaklar.
> Çalışma şekli (online / hibrit / yüz yüze), bölge–il–ilçe seçimi, pozisyon,
> deneyim, istihdam türü filtreleri.
>
> Bu dosya `PLAN_KARIYER.md`'nin (kaynak envanteri) **üstüne** gelen uygulama
> yol haritasıdır. O dosya "hangi kaynaklar" sorusunu, bu dosya "hangi sırayla,
> nasıl, ne zaman bitti" sorusunu cevaplar.

---

## 0. Çalışma protokolü — DURMADAN İLERLEME

Bu bölüm plandaki en önemli kısım. Amaç: onay beklemeden ilerleyebilmek.

1. **Her zaman en üstteki `[ ]` görevi al.** Görevler bağımsız tasarlandı;
   birini bitirmeden diğerine geçme.
2. **Karar gerektiren her yerde varsayılan önceden verildi** (§4 "Kararlar").
   Onay bekleme; varsayılanı uygula, farklı bir şey yaptıysan sebebini
   `GOREVLER.md`'ye yaz.
3. **Bir kaynak tıkanırsa DURMA.** §3'teki erişim karar ağacını uygula. Hâlâ
   olmuyorsa görevi `[!]` işaretle, tek satır sebep yaz, **sıradakine geç.**
   Tıkalı kaynak toplam ilerlemeyi bloke etmez.
4. **Her görevin sonunda:** ruff temiz + pytest yeşil + `GOREVLER.md` güncel +
   commit. Yarım bırakma.
5. **Veri dosyasına asla korumasız yazma** — `_guard.py` zorunlu (§5).

---

## 1. Kanonik veri modeli (şema v2)

Mevcut şema (`id, hat, kaynak, baslik, kurum, sehir, tarih, url, ozet, detay,
ilk_gorulme, bolumler`) yetersiz: çalışma şekli, bölge, deneyim, istihdam türü
yok. **Önce şema, sonra kaynaklar** — yoksa her yeni kaynakta geriye dönük
düzeltme gerekir.

```jsonc
{
  "id": "kaynak:dogal_anahtar",      // ör. "ilangovtr:ILN02540130"
  "kaynak": "ilan.gov.tr",           // insan-okur kaynak adı
  "kaynak_kod": "ilangovtr",         // kayıt defterindeki slug
  "hat": "kamu",                     // kamu | ozel
  "kpss": true,                      // KPSS şartı var mı (bilinmiyorsa null)
  "baslik": "...",
  "kurum": "...",                    // işveren / kurum
  "il": "İSTANBUL",                  // BÜYÜK, TR normalize
  "ilce": "Kadıköy",
  "bolge": "Marmara",                // il'den TÜRETİLİR (§2)
  "calisma_sekli": "yuzyuze",        // online | hibrit | yuzyuze | bilinmiyor
  "istihdam_turu": "tam_zamanli",    // tam_zamanli|yari_zamanli|staj|sozlesmeli|gecici|bilinmiyor
  "deneyim": "yeni_mezun",           // yeni_mezun|0_2|2_5|5_plus|bilinmiyor
  "pozisyon_etiket": ["yazilim"],    // normalize meslek etiketleri
  "bolumler": ["bilgisayar-muh"],    // mevcut bölüm eşleştirme korunur
  "maas": null,                      // {"min":..,"max":..,"para":"TRY"} | null
  "tarih": "2026-09-05",             // yayın tarihi
  "son_basvuru": "2026-09-20",       // varsa
  "url": "https://...",              // ORİJİNAL ilana link (zorunlu)
  "ozet": "...",                     // en fazla ~300 karakter
  "ilk_gorulme": "2026-09-05",
  "detay": {}                        // kaynağa özgü ham alanlar
}
```

**Kurallar**

- `id` çakışması = aynı ilan. Farklı kaynaktan gelen aynı ilan için §4 tekilleştirme.
- Tam ilan metni **kopyalanmaz** (telif). Başlık + kısa özet + orijinal link.
- Kişisel veri saklanmaz (KVKK). İletişim bilgisi alınmaz.
- `bilinmiyor` meşru bir değerdir; uydurma yapma.

---

## 2. Bölge tablosu (il → bölge)

Frontend'deki "bölge seçimi" bunun üzerine kurulur. `domain/geo.py` zaten var;
yeni dosya açma, oraya ekle. 81 il eksiksiz eşlenir, il adları TR-normalize
(büyük harf, İ/I ayrımı korunur).

Bölgeler: Marmara, Ege, Akdeniz, İç Anadolu, Karadeniz, Doğu Anadolu,
Güneydoğu Anadolu.

---

## 3. Erişim karar ağacı — "aracı olmayan siteyi nasıl çekeriz"

Bir kaynak için **sırayla** dene, ilk çalışanda dur:

1. **Resmî/açık JSON API** → en iyi. Tarayıcı ağ sekmesiyle bulunur; SPA siteler
   neredeyse her zaman bir API'ye konuşur.
2. **RSS / Atom feed** → `/rss`, `/feed`, `/rss.xml`, sayfadaki
   `<link rel=alternate>`.
3. **Sitemap** → `robots.txt` içindeki `Sitemap:` satırları; `daily-*.xml` varsa
   günlük delta için idealdir.
4. **Sunucu tarafı HTML** → `curl` ile anlamlı içerik geliyorsa parse et.
5. **Chunked-hang / çok yavaş sunucu** → `_osym.fetch_tolerant()` desenini
   kullan (gövde akıtılır, sunucu bağlantıyı kapatmasa da eldekiyle devam
   edilir). ÖSYM'de 240 sn timeout → **1.0 saniyeye** düştü.
6. **WAF / bot koruması** (403, "Request Rejected", CAPTCHA) → **kazımaya
   ZORLAMA.** Sırasıyla: resmî ayna (İŞKUR→MEB aynası emsali,
   `iskur_mbk_scraper.py`), üçüncü taraf toplayıcı (Jooble/Careerjet API),
   kurumun kendi RSS/duyuru sayfası; olmuyorsa `[!]` işaretle ve geç.
7. **Hiçbiri yoksa** → kayıt defterine `erisim: yok` + sebep yaz, sıradakine geç.

**Uyulacaklar:** `robots.txt`'e uy; User-Agent gerçekçi ve sabit; istekler arası
en az 1 sn bekle; aynı kaynağa günde tek koşu; oturum/giriş gerektiren yerlere
girme.

### 3.1 Yapılmış keşifler (2026-09-05, Claude Code — bunları tekrar araştırma)

| Kaynak | Durum | Bulgu / yöntem |
|---|---|---|
| **ilan.gov.tr** | 🟡 **API bulundu, oturum şartı çözülmedi** | Uç nokta: `POST https://www.ilan.gov.tr/api/api/services/app/Ad/AdsByFilter`. **Doğrulanmış kayıt şeması** (sitenin kendi isteğinin yanıtından alındı): `result.ads[]` → `id, adNo, advertiserName, title, slugifyTitle, addressCityName, addressCountyName, publishStartDate, urlStr, adSourceName, adTypeFilters[{key,value}]`; ayrıca `result.cityCounts` (şehir kırılımı — bölge filtresi için birebir) ve `result.numFound` (**25.062** ilan). **DİKKAT — yanlış ize düşme:** aynı gövde (`{skipCount, maxResultCount, sorting:"publishDate desc"}`) ilk denemelerde 25.062 döndürdü, sonraki tüm denemelerde (ana sayfa dahil) **0** döndü. Yani uç nokta anonim değil: bir oturum çerezi / ABP token / `Referer` başlığı ya da hız sınırı devrede. **Yapılacak:** tarayıcıda tek bir başarılı isteğin TAM başlıklarını + gövdesini yakala (fetch monkey-patch tam sayfa gezinmede siliniyor; `Ctrl+Shift+I → Network → Copy as cURL` en pratiği), sonra Python'da birebir tekrarla. `ats=5` = PERSONEL ALIMI (URL'den: `/ilan/tum-ilanlar/personel-alimi?ats=5`, `kategori/8/kamu-akademik-personel?ats=5`) — gövdedeki karşılığı bu yakalamada görülecek. robots.txt yalnız `/*tebligat` yasaklıyor. |
| ilan.gov.tr sitemap | ❌ | robots.txt `ads.xml`, `daily-ads.xml` ilan ediyor ama hepsi **404**. Kullanma. |
| **İŞKUR e-Şube** | ❌ WAF | `robots.txt` bile "Request Rejected" dönüyor. Doğrudan erişim yok — §3 madde 6. |
| kamuilan.sbb.gov.tr | 🟡 | HTTP 200, ~207 KB sunucu-tarafı HTML → parse edilebilir. Arşiv niteliğinde, başvuru alınmaz. |
| TÜBİTAK kariyer | 🟡 | HTTP 200, ~22 KB. İncelenecek. |
| Vizyoner Genç | 🟡 | HTTP 200 ama ~1.5 KB → SPA kabuğu. API'si ağ sekmesiyle aranmalı. |
| Kariyer Kapısı | ❓ | `kariyerkapisi.gov.tr` bu makineden çözülemedi. Runner'dan veya tarayıcıdan tekrar denenmeli; **en kritik kamu kanalı (A1).** |
| ÖSYM | ✅ çözüldü | `_osym.py` hazır: `fetch_tolerant` + `/Duyurular/Index` keşfi. Kariyer için yeniden kullan. |

---

## 4. Önceden verilmiş kararlar (onay bekleme)

| Konu | Karar |
|---|---|
| Kapsam | Yeni mezun/staj **ağırlıklı değil** — tüm seviyeler. Süzme kullanıcıda. |
| Cron saati | Günlük `0 5 * * *` UTC (mevcut `kariyer-sync.yml`). Kaynak sayısı artınca 2 koşuya böl. |
| Saklama | İlan 30 gün sonra budanır (mevcut davranış korunur). |
| Kaynak kayıt defteri | Kod değil **veri**: `backend/data/kaynaklar/is_kaynaklari.yml`. Yeni kaynak = YAML girdisi + adaptör. |
| Adaptör deseni | `scrapers/kariyer/<kaynak_kod>.py`, tek giriş: `fetch(session) -> list[dict]`. |
| Tekilleştirme | `id` birebir; ayrıca `(normalize(baslik), kurum, il)` çakışırsa **kamu hattı kazanır** (resmî kaynak önceliklidir). |
| API anahtarı gereken kaynak | Anahtar yoksa `[!]` + `erisim: anahtar_yok`. Anahtar isteme, not düş. |
| Frontend | Mevcut `Kariyer.jsx` genişletilir; yeni sayfa açılmaz. |

---

## 5. Değişmez kurallar

- **Bekçi zorunlu.** Her scraper `_guard.py` kullanır: boş sonuç veya %50'den
  fazla küçülme → dosyaya dokunma, `exit 1`. Sebep: `kpss_placements.json`
  27 Temmuz'da 1 MB'tan `[]` oldu, workflow "success" dedi, 6 hafta fark edilmedi.
- **Sessiz başarı yasak.** Hiçbir kaynak veri üretemezse `exit 1`.
- **Kısmi başarı normal.** 12 kaynaktan 9'u çalışıyorsa koşu başarılıdır; düşen
  kaynak log'a ve `detay.kosu_raporu`'na yazılır.
- **Mevcut `/api/v1/*` yolları değişmez.** Yeni alanlar eklenir, eskiler kalır.
- **`backend/data/` elle commit'lenmez** — pipeline üretir.

---

## 6. Görev sırası

Her görev bağımsız ve tanımlı bitişi var. Sırayla ilerle.

### F0 — Temel (önce bu; yoksa her kaynak geriye dönük düzeltme ister)

- [ ] **F0.1** Şema v2'yi uygula. Mevcut kayıtları taşıyan `_migrate()` yaz
      (eksik alanlar `bilinmiyor`/`null`).
      *Bitti:* mevcut 488 kayıt kayıpsız v2'ye geçti, pytest yeşil.
- [x] **F0.2** ~~81 il → bölge tablosu~~ **BİTTİ (Claude Code, 2026-09-05).**
      `REGIONS` + `il_to_bolge()` zaten vardı ama düz `.upper()` kullanıyordu:
      "Istanbul" (ASCII I) ve "istanbul" → "Bilinmiyor" dönüyordu, yani bölge
      filtresi yabancı API verisinde sessizce boş kalırdı. Aksan-katlamalı
      indeks eklendi; "İSTANBUL"/"Istanbul"/"istanbul"/" İstanbul " hepsi
      "Marmara". 81 ilin tamamı eşleşiyor, `tests/test_geo_bolge.py` (18 test).
      Adaptörler `il_to_bolge(il)` çağırıp `bolge` alanını doldurabilir.
- [ ] **F0.3** `calisma_sekli` çıkarımı: başlık+özette "uzaktan / remote / hibrit /
      home office / yerinde" kalıpları. Bulunamazsa `bilinmiyor`.
      *Bitti:* kalıp tablosu testli, mevcut kayıtlardaki dağılım log'lanıyor.
- [ ] **F0.4** Kaynak kayıt defteri `is_kaynaklari.yml` + adaptör yükleyici.
      Alanlar: `kod, ad, hat, url, erisim(api|rss|sitemap|html|toleransli|yok),
      aktif, not`. Jooble/Careerjet/Resmî Gazete bu deftere taşınır.
      *Bitti:* `kariyer_scraper.py` kaynakları defterden okuyor, davranış aynı.

### F1 — Kamu hattı (en yüksek değer; KPSS'li + KPSS'siz)

- [ ] **F1.1** `ilangovtr` adaptörü. **İlk adım: oturum şartını çöz** (§3.1'deki
      "Copy as cURL" tarifi) — şema ve `cityCounts` zaten doğrulandı, eksik olan
      yalnızca isteğin kabul edilmesi. Çözülemezse `[!]` yaz ve F1.2'ye geç;
      §3 madde 4 (sunucu-tarafı HTML) alternatifini dene.
      *Bitti:* ≥200 personel-alımı ilanı v2 şemasında, il/ilçe dolu.
- [ ] **F1.2** Kariyer Kapısı (A1) erişimi — runner'dan/tarayıcıdan tekrar dene,
      §3 ağacını uygula. **En kritik kamu kanalı.**
- [ ] **F1.3** Vizyoner Genç (A9) — SPA; API'si ağ sekmesiyle bulunacak.
      KPSS'siz savunma sanayii ilanları.
- [ ] **F1.4** kamuilan.sbb.gov.tr (A4) — sunucu-tarafı HTML parse.
- [ ] **F1.5** ilan.yok.gov.tr (A8) — akademik kadro.
- [ ] **F1.6** TÜBİTAK + kurum portalları (A10/A13/A14): HAVELSAN, ASELSAN,
      TÜRKSAT, STM, Ziraat Teknoloji. Her biri ayrı adaptör, aynı desen.
- [ ] **F1.7** İŞKUR (A6) — WAF'lı. §3 madde 6: resmî ayna / toplayıcı üzerinden.
      Olmuyorsa `[!]` işaretle, geç.
- [ ] **F1.8** `kpss` alanı: ilan metninde "KPSS" geçiyor mu + puan türü
      (P3/P93/P94) çıkarımı. Mevcut `kpss_service` ile bağ kurulabilir.

### F2 — Özel sektör hattı

- [ ] **F2.1** Jooble + Careerjet adaptörlerini deftere taşı; sorgu listesini
      genişlet (yalnız mühendislik değil — tüm meslek grupları).
- [ ] **F2.2** Şirket kariyer sayfaları (`PLAN_KARIYER.md` Hat B, ~50 şirket).
      **Verimli yol:** önce ATS tespiti (Lever / Greenhouse / Workable) —
      aynı ATS'i kullanan şirketler **tek adaptörle** çekilir.
- [ ] **F2.3** kariyer.net / secretcv / yenibiris / eleman.net — bot koruması
      beklenir. §3 madde 6; zorlama.

### F3 — API ve filtreler

- [ ] **F3.1** `GET /api/v1/kariyer/ilanlar` filtreleri: `hat, il, bolge, ilce,
      calisma_sekli, istihdam_turu, deneyim, kpss, q, sayfa, boyut`.
- [ ] **F3.2** `GET /api/v1/kariyer/filtreler` — mevcut değerler + sayıları
      (facet). Frontend filtre panelini bu besler.
- [ ] **F3.3** Sıralama: `tarih desc` (varsayılan), `son_basvuru asc`.

### F4 — Frontend (Kariyer.net / Indeed hissi)

- [ ] **F4.1** Filtre paneli: bölge → il → ilçe kademeli seçim; çalışma şekli
      çoklu seçim; istihdam türü; deneyim; KPSS var/yok anahtarı.
- [ ] **F4.2** Arama kutusu (başlık + kurum); filtre durumu URL'ye yansısın
      (paylaşılabilir link).
- [ ] **F4.3** İlan kartı: kurum, il/ilçe, çalışma şekli rozeti, tarih,
      "bugün yeni" rozeti, son başvuru sayacı.
- [ ] **F4.4** Mobil: 360px'te taşmasız; filtre paneli çekmece.
- [ ] **F4.5** Boş durum + yükleniyor durumu; sonuç sayısı görünür.

### F5 — Dayanıklılık ve gözlemlenebilirlik

- [ ] **F5.1** Kaynak bazlı koşu raporu: kaç ilan, kaç yeni, kaç hata →
      `detay.kosu_raporu`.
- [ ] **F5.2** Bir kaynak 3 koşu üst üste 0 üretirse workflow uyarsın
      (sessizce ölen kaynak = fark edilmeyen kayıp).
- [ ] **F5.3** Kaynak sayısı 15'i geçince cron'u 2 koşuya böl (kamu / özel).

---

## 7. Bu plan bittiğinde

Kullanıcı tek sayfadan: bölge/il/ilçe seçip, online veya yüz yüze filtreleyip,
kamu (KPSS'li/KPSS'siz) ve özel sektör ilanlarını birlikte görebilir; her ilan
orijinal kaynağına gider. Günlük cron yeni ilanları getirir, eskiler budanır,
hiçbir kaynak sessizce ölmez.
