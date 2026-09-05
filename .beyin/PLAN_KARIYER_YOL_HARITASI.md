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

**e-Devlet / giriş duvarı — kesin kural.** Kamu portallarında e-Devlet girişi
**BAŞVURU** içindir, **İLAN LİSTESİ** için değil. Bir sayfa giriş istiyor gibi
duruyorsa önce listeyi giriş olmadan denemek gerekir; çoğu zaman açıktır
(Kariyer Kapısı bunun kanıtı: `/RSS` herkese açık, 33 ilan).

- e-Devlet/OAuth girişi **ASLA otomatikleştirilmez.** Kimlik bilgisi girilmez,
  oturum taklit edilmez, çerez çalınmaz. Hem yasal/ToS riski hem de gereksiz.
- Modelimiz: **ilanı biz gösteririz, başvuruya kaynağa yönlendiririz.** §1'deki
  "orijinal ilana link zorunlu" kuralı zaten bunu söylüyor.
- Gerçekten giriş arkasındaki bir liste varsa o kaynak `erisim: giris_gerekli`
  ile işaretlenir ve **atlanır** — kullanıcıya kaynağın linki gösterilir.

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
| **Kariyer Kapısı** | ✅ **RSS bulundu** | `https://kariyerkapisi.gov.tr/RSS` → `application/xml`, **33 ilan**, GİRİŞ GEREKTİRMİYOR. Alanlar: `title` ("KURUM - İlan adı"), `category` ("Sözleşmeli Personel İlanları" vb.), `link`/`guid` (`/IlanDetay?i=<uuid>`), `pubDate` (RFC-822). Sayfada `robots: index, follow`. e-Devlet bağlantısı yalnız **başvuru** içindir (`giris.turkiye.gov.tr/OAuth2...`), listeyi engellemiyor. **DNS UYARISI:** `kariyerkapisi.gov.tr` bu makinenin yerel çözümleyicisinde çözülmüyor ama 8.8.8.8/1.1.1.1 çözüyor (94.55.123.141) — yerel ISS sorunu, CI runner'da olmayacak. Yerelde denemek için `curl --resolve kariyerkapisi.gov.tr:443:94.55.123.141`. |
| ÖSYM | ✅ çözüldü | `_osym.py` hazır: `fetch_tolerant` + `/Duyurular/Index` keşfi. Kariyer için yeniden kullan. |


### 3.1.b İl/bölge kapsamı — `KAYNAK_HARITASI.md`

81 il kapsamı için ayrı bir keşif dosyası var: **`.beyin/KAYNAK_HARITASI.md`**.
Özeti: kurum-kurum gitmek çalışmaz (ortak URL deseni yok, üniversite siteleri
soft-404 veriyor), çünkü kamu ilanları için **yasal olarak zorunlu merkezî
portal** var — BİK/ilan.gov.tr 81 ildeki resmî ilanları tek merkezden yönetiyor
ve Hatay Büyükşehir örneğiyle canlı doğrulandı. **Toplayıcı önce**, kurum-kurum
yalnız toplayıcının kapsamadığı boşluklar için.

### 3.2 KAPALI KAPILAR — denenmeyecek kaynaklar (2026-09-05 ölçüldü)

Bunlar "henüz yapılmadı" değil, **yapılmayacak**. Vakit harcama, tekrar deneme.

| Kaynak | Kanıt | Karar |
|---|---|---|
| **LinkedIn** | `robots.txt`: `User-agent: *` → `Disallow: /` (tüm site). Ayrıca `User-agent: anthropic-ai` → `Disallow: /` ile bize özel yasak. 4398 kural, 33 tam-yasak bloğu. Dosyada not: "crawl etmek istiyorsan whitelist-crawl@linkedin.com'a yaz." | **KULLANILMAYACAK.** Hat B listesinden çıkarıldı. İzin alınmadan tek satır çekilmez. |
| **İŞKUR e-Şube** | `robots.txt` bile "Request Rejected" (WAF). | Doğrudan erişim yok. Yalnız resmî ayna / toplayıcı üzerinden (§3 madde 6). |
| **e-Devlet arkası her şey** | — | Giriş **asla** otomatikleştirilmez (§3 kuralı). Liste açıksa alınır, değilse kaynak atlanır. |

**Kısıtlı ama mümkün olanlar** (adaptör yazmadan önce yol bazında robots kontrolü ZORUNLU):

| Kaynak | Durum |
|---|---|
| tr.indeed.com | 468 disallow kuralı, 128'i ilan/arama yollarında (`/advanced_search`, `/api/getrecjobs`, ülke bazlı `/jobs/XX/`). Türkiye yolları ayrıca teyit edilmeli. |
| kariyer.net | `User-agent: *` altında 45 disallow ama **ilan yolları yasak DEĞİL**. Yasaklı: `/filtre`, `/filtre/*`, `/ozgecmis/*`, `/Services/`, `/WebSite/Kariyerim/`. Yani ilan listesi robots açısından serbest; filtre URL'leri kullanılmaz. |
| secretcv.com / eleman.net | 18-20 kural, 4'ü ilan/arama yollarında. Yol bazında bakılmalı. |
| yenibiris.com | 21 kural, ilan/arama yolunda yasak yok. |

> **Kural:** robots izin veriyor diye site kazımayı *hoş karşılıyor* demek değil.
> WAF/CAPTCHA çıkarsa §3 madde 6 uygulanır — zorlanmaz.

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

- [x] **F0.1** Şema v2'yi uygula (opencode, 2026-09-05, 8ebe2f8). Mevcut kayıtları
      taşıyan `_migrate()` yazıldı (eksik alanlar `bilinmiyor`/`null`).
      *Bitti:* 487 kayıt kayıpsız v2'ye geçti, pytest yeşil.
- [x] **F0.2** ~~81 il → bölge tablosu~~ **BİTTİ (Claude Code, 2026-09-05).**
      `REGIONS` + `il_to_bolge()` zaten vardı ama düz `.upper()` kullanıyordu:
      "Istanbul" (ASCII I) ve "istanbul" → "Bilinmiyor" dönüyordu, yani bölge
      filtresi yabancı API verisinde sessizce boş kalırdı. Aksan-katlamalı
      indeks eklendi; "İSTANBUL"/"Istanbul"/"istanbul"/" İstanbul " hepsi
      "Marmara". 81 ilin tamamı eşleşiyor, `tests/test_geo_bolge.py` (18 test).
      Adaptörler `il_to_bolge(il)` çağırıp `bolge` alanını doldurabilir.
- [x] **F0.3** `calisma_sekli` çıkarımı (opencode, 2026-09-05, 9fab443):
      hibrit > online > yuzyuze kalıp tablosu + normalize ve geriye dönük
      v2 çıkarımı. *Bitti:* kalıp tablosu testli (5 test), canlı dağılım
      loglandı: 486 kayıtta 480 bilinmiyor / 2 online / 4 yuzyuze
      (snippet'lar kısa; `bilinmiyor` meşru değer).
- [x] **F0.4** Kaynak kayıt defteri `is_kaynaklari.yml` + adaptör yükleyici
      (opencode, 2026-09-05, 7d6dec3). Jooble/Careerjet/Resmî Gazete deftere
      taşındı. *Bitti:* `kariyer_scraper.py` kaynakları defterden okuyor,
      davranış aynı (canlı 486 kayıt, dağılım değişmedi).

### F1 — Görünür değer: filtreler ve arayüz (ÖNCE BU)

> **Sıra 2026-09-05'te değiştirildi (Claude Code).** Önceki sürümde API ve
> frontend, 11 kaynak görevinin ARKASINDAYDI. Ama F0 bitince mevcut ~490 kayıt
> zaten `il` / `bolge` / `calisma_sekli` taşıyor — yani kullanıcının istediği
> bölge ve çalışma şekli filtresi BUGÜN çalışabilir durumda. Değeri kaynak
> sayısının arkasında kilitlemek yanlıştı. Önce çalışan bir ürün, sonra kaynak
> genişletme.

- [x] **F1.1** `GET /api/v1/kariyer/ilanlar` filtreleri (opencode, 2026-09-05,
      2c99e58): `hat, il, bolge, ilce, calisma_sekli, istihdam_turu, deneyim,
      kpss, q, sayfa, boyut` + legacy `limit`.
      *Bitti:* her filtre canlı veride doğru sayı döndürüyor, mevcut çağrılar
      bozulmadı, testli.
- [x] **F1.2** `GET /api/v1/kariyer/filtreler` (opencode, 2026-09-05, 2c99e58).
      *Bitti:* bölge/il/çalışma şekli facet'leri gerçek sayılarla dönüyor.
- [x] **F1.3** Sıralama (opencode, 2026-09-05, 2c99e58): `tarih desc`
      (varsayılan), `son_basvuru asc` (tarihsizler sonda).
- [x] **F1.4** Filtre paneli (opencode, 2026-09-05, aaf76f9): bölge → il → ilçe
      kademeli seçim (facet `bolge` alanıyla); çalışma şekli çoklu seçim
      (API liste-parametreye genişletildi); KPSS 3-durum anahtarı.
      Not: istihdam/deneyim panelde yok — veride yalnız `bilinmiyor` var,
      API destekliyor; veri gelince panel genişler.
- [x] **F1.5** Arama kutusu (opencode, 2026-09-05, aaf76f9): başlık + kurum;
      TÜM filtre durumu URL'de (`useSearchParams`) — paylaşılabilir link.
- [x] **F1.6** İlan kartı (opencode, 2026-09-05, aaf76f9): kurum, il/ilçe,
      çalışma şekli rozeti, tarih, "yeni" rozeti, son başvuru sayacı
      (son X gün / son gün / süresi dolmuş).
- [x] **F1.7** Mobil (opencode, 2026-09-05, aaf76f9): 360px grid'ler tek sütuna
      iniyor (mevcut shell), filtre paneli çekmece (mobilde kapalı, `aktif`
      rozeti), boş durum + temizleme butonu + sonuç sayısı.

### F2 — Kaynak eklemeden ÖNCE gereken emniyet

> Bu üçü F3/F4'ten önce çünkü 11 kaynak eklemeye başlayınca artık geç olur:
> hangi kaynağın sessizce öldüğünü göremezsin ve mükerrer ilanlar birikir.

- [x] **F2.1** Kaynak bazlı koşu raporu (opencode, 2026-09-05, a912594): her
      kaynak için çekilen/yeni/hata → `kariyer_kosu.json` + log satırları +
      `meta.son_kosu`; adaptör hataları koşuyu düşürmüyor (kısmi başarı).
      *Bitti:* canlı 4 kaynak satırı görünüyor.
- [x] **F2.2** Bir kaynak 3 koşu üst üste 0 üretirse workflow uyarsın
      (opencode, 2026-09-05, 7660aea). `kariyer_kosu.json`'da 10 koşuluk geçmiş
      + `alarm` listesi; log'da 🚨 + Actions Step Summary özeti. Karar: cron'u
      kırmızıya düşürmez (flaky alarm yorgunluğu; toplam-boşta guard zaten
      exit 1 verir).
- [x] **F2.3** **Çapraz kaynak tekilleştirme** (opencode, 2026-09-05, da93be9).
      `id` birebir; ayrıca `(normalize(baslik), kurum, il)` çakışırsa **kamu
      hattı kazanır**, etiketler birleşir, ilk_gorulme korunur.
      *Bitti:* sentetik veriyle testli (kamu-kazanır + boş-alan güvenliği +
      il ayrımı) + canlı 17 birleşme.

### F3 — Kamu hattı (KPSS'li + KPSS'siz)

> **Sıra bilinçli:** önce erişimi KESİN olan kaynaklar. Önceki sürümde ilk iki
> görev de belirsizdi (ilan.gov.tr oturum şartı çözülmemiş, Kariyer Kapısı DNS
> çözülemiyor) — adaptör deseni oturmadan iki bilinmeyene çarpmak momentum kırar.

- [x] **F3.1** **Kariyer Kapısı (A1) — RSS adaptörü** (opencode, 2026-09-05,
      74bd5ea). Girişsiz `/RSS` doğrulandı (33 ilan, yapılandırılmış).
      *Bitti:* 30 ilan v2 şemasında, `kurum` ve `tarih` dolu, bekçi devrede.
- [x] **F3.2** kamuilan.sbb.gov.tr (opencode, 2026-09-05, 46368bb) — boş-arama
      postback'i + `ul#nav2` timeline parse (kurum, başlık, tarih, son_basvuru,
      bölüm etiketleri). *Bitti:* canlı 76 ilan (68'i pencerede), v2 şemalı,
      testli (34 kariyer testi).
- [x] **F3.3** ~~ilan.yok.gov.tr (A8) — akademik kadro~~ **İPTAL
      (Claude Code, 2026-09-05).** Öyle bir adres yok. Akademik kadro zaten
      BİK'te: kategori `73` (akademik-personel-alimlari) ve `8`
      (kamu-akademik-personel). Sağlık alımları da aynı şekilde toplayıcıda.
      → K1 adaptörü (F3.4) bu kategorileri de çekince kapsanır; ayrı adaptör
      gereksiz. Ayrıntı: `KAYNAK_HARITASI.md` §6.1-6.2.
      (opencode notu, 2026-09-05: akademiktr adaptörü çalışıyor — 32 kayıt
      canlıda; F3.4 kat.73/8 kapsamı doğrulanınca kaldırılacak.)
- [x] **F3.4** `ilangovtr` adaptörü (opencode, 2026-09-05, b18ebbe) — tarif
      doğrulandı, 126 personel ilanı canlı. Not: artımlı erken-duruş ilk
      sürümde eski kayıtları siliyordu → union merge + `ILANGOVTR_TAM_TARAMA`
      bayrağı ile düzeltildi.
      ⚠️ `id desc` KRONOLOJİK DEĞİL (skip 0'da 2022, skip 100'de 2026 kaydı) —
      "görülen id'ye gelince dur" stratejisi KAÇIRMA yapar. Personel ilanları
      dağınık (ilk 1.600'de 23 tane, derin arşivde sıfır) → tam tarama veya
      gerçek kategori süzgeci gerekir. Ayrıntı: `KAYNAK_HARITASI` §11.5-DÜZELTME.
      *Bitti:* personel alımı ilanları v2 şemasında, il/ilçe dolu,
      `cityCounts` facet olarak saklanmış.
- [ ] **F3.5** **Savunma Kariyer** (eski adı Vizyoner Genç — site
      `savunmakariyer.com`'a taşınmış). **API TAMAMEN ÇÖZÜLDÜ**, keşif gerekmez
      (`KAYNAK_HARITASI.md` §10): `POST /api/career-core/public/jobs`
      `{"page":1,"size":100}` → 24 ilan; `GET /api/common/public/city` → 81 il;
      `GET /api/corporate/public/approved-companies?page=1&size=200` → 343 firma.
      Kimlik doğrulama yok. `jobLocation` il veriyor, `endDate` son başvuru.
      *Bitti:* 24 ilan v2 şemasında, `il`/`bolge`/`son_basvuru` dolu.
- [ ] **F3.6** Kurum portalları — **kapsam DARALDI.** F3.5'teki tek adaptör
      ASELSAN, HAVELSAN, ROKETSAN, STM, BAYKAR, TUSAŞ, TEI, MKE, FNSS, Nurol'ü
      zaten getiriyor (§10.3). **Önce F3.5'i bitir, sonra neyin eksik kaldığını
      ÖLÇ.** Geriye muhtemelen yalnız TÜBİTAK, Türksat, Ziraat Teknoloji kalır.
      *Bitti:* F3.5 sonrası eksik kurum listesi ölçülmüş ve yalnız onlar için
      adaptör yazılmış.
- [ ] **F3.7** İŞKUR (A6) — WAF teyitli. §3 madde 6: resmî ayna / toplayıcı.
      Olmuyorsa `[!]` işaretle, geç.
- [ ] **F3.8** `kpss` alanı: ilan metninde "KPSS" geçiyor mu + puan türü
      (P3/P93/P94) çıkarımı. Mevcut `kpss_service` ile bağ kurulabilir.

### F4 — Özel sektör hattı

- [ ] **F4.1** Jooble + Careerjet sorgu listesini genişlet — şu an yalnız
      mühendislik ağırlıklı; tüm meslek gruplarını kapsasın.
- [ ] **F4.2** **ATS tespiti** (araştırma): Hat B'deki ~50 şirketin hangisi
      Lever / Greenhouse / Workable kullanıyor, listele.
      **Uç noktalar doğrulandı** (`KAYNAK_HARITASI.md` §9.2):
      Lever `api.lever.co/v0/postings/<slug>?mode=json` (Dream Games → 19 ilan),
      Greenhouse `boards-api.greenhouse.io/v1/boards/<slug>/jobs`. Kimlik
      doğrulama yok; Lever kaydında konum + çalışma şekli + takım hazır geliyor.
      ⚠️ **Slug TAHMİN ETME** — `insider` slug'ı ABD'li aynı adlı şirketi
      getirdi (New York/Singapore ilanları). Şirketin kariyer sayfasındaki
      bağlantıyı OKU, ayrıca çekilen konumları `il_to_bolge` ile doğrula.
      *Bitti:* şirket → ATS eşlemesi `is_kaynaklari.yml`'de, her eşleme
      konum doğrulamasından geçmiş.
- [ ] **F4.3** Tespit edilen her ATS için **tek adaptör** yaz (Lever, Greenhouse,
      Workable). En verimli yol: bir adaptör onlarca şirketi çeker.
      *Bitti:* en az bir ATS üzerinden ≥3 şirketin ilanları geliyor.
- [ ] **F4.4** ATS kullanmayan şirketler için tek tek adaptör — F4.2'deki
      listeden, önce ilan sayısı yüksek olanlar.
- [ ] **F4.5** kariyer.net / secretcv / yenibiris / eleman.net.
      **Ön koşul:** adaptör yazmadan önce hedef YOLU `robots.txt`'te doğrula
      (§3.2 tablosu). kariyer.net'te ilan yolları serbest ama `/filtre*` ve
      `/ozgecmis/*` YASAK — filtre URL'leri kullanılmayacak.
      Bot koruması çıkarsa §3 madde 6; zorlanmaz.
      *Bitti:* her kaynak için "robots izni var mı" kararı kayıt defterine
      `robots_kontrol` alanı olarak yazıldı.
- [ ] **F4.6** tr.indeed.com — 468 disallow kuralı var, ilan/arama yollarının
      çoğu kapalı. **Önce** Türkiye ilan yollarının serbest olup olmadığını
      belirle; kapalıysa `erisim: robots_yasak` yaz ve GEÇ.
      **LinkedIn bu fazda YOK** — §3.2'ye göre kalıcı olarak kapalı.

### F5 — Ölçekleme

- [ ] **F5.1** Kaynak sayısı 15'i geçince cron'u 2 koşuya böl (kamu / özel).
- [ ] **F5.2** Kaynak başına hız sınırı ve yeniden deneme politikası tek yerde
      toplansın (şu an adaptörlere dağılmış olabilir).
- [ ] **F5.3** **Repo şişmesi — ölçüldü, ilerde tıkar.** Repo şu an **230 MB**.
      `chunks.json` 28 MB ve her index yeniden üretiminde commit'leniyor;
      `kariyer_ilanlar.json` 528 KB ve GÜNLÜK commit'leniyor (yılda ~365 sürüm).
      Klonlama ve CI checkout süresi büyümeye devam eder.
      *Seçenekler:* (a) büyük veri dosyalarını git yerine HF dataset'te tut
      (index-sync zaten HF kullanıyor — aynı deseni kariyer verisine uygula),
      (b) günlük tam dosya yerine delta commit, (c) veri dosyalarını ayrı repoya
      taşı. **Karar kullanıcıya ait**, seçenekleri ölçümle birlikte sun.
      *Bitti:* seçim yapıldı ve uygulandı; günlük commit boyutu ölçülüp yazıldı.

## 7. Bu plan bittiğinde

Kullanıcı tek sayfadan: bölge/il/ilçe seçip, online veya yüz yüze filtreleyip,
kamu (KPSS'li/KPSS'siz) ve özel sektör ilanlarını birlikte görebilir; her ilan
orijinal kaynağına gider. Günlük cron yeni ilanları getirir, eskiler budanır,
hiçbir kaynak sessizce ölmez.
