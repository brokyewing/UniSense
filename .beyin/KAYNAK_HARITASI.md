# Kaynak Haritası — 81 İl / Bölge Bazlı İş İlanı Taraması

**Yazan:** Claude Code (keşif) · **Tarih:** 2026-09-05
**Kime:** opencode (birleştirme ve adaptör yazımı ona ait)
**Kapsam:** Bu dosya YALNIZCA keşiftir — hangi kaynak var, nasıl erişilir,
neyi kapsar. Kod yazımı ve birleştirme yol haritasının F3/F4 fazlarında.

---

## 1. Ana bulgu — kurum kurum gitmek ÇALIŞMAZ

Kullanıcının isteği "Hatay'daki kurumların hepsinin kendi iş sayfası, 81 il için"
şeklindeydi. Bunu doğrudan denemek sürdürülemez; ölçtüm:

**Ortak URL deseni yok.** 4 büyükşehir belediyesinde `/ilanlar`, `/duyurular`,
`/insan-kaynaklari`, `/kariyer`, `/rss` yolları denendi:

| Site | /ilanlar | /duyurular | /insan-kaynaklari | /rss | /kariyer |
|---|---|---|---|---|---|
| hatay.bel.tr | 200 | 200 | 404 | 404 | 404 |
| ankara.bel.tr | 200 | 200 | 200 | 200 | 200 |
| izmir.bel.tr | 404 | 404 | 404 | 404 | 404 |
| konya.bel.tr | 404 | 404 | 404 | 404 | 404 |

**Üstelik 200'lerin bir kısmı SAHTE.** Uydurma bir yol (`/boyle-bir-sayfa-yok-12345`)
denendiğinde:

- `mku.edu.tr` → **200** (soft-404)
- `ege.edu.tr` → **200** (soft-404)
- `hatay.bel.tr` → 404 (dürüst)

Yani üniversite sitelerinde HTTP durum koduna güvenilemez; "sayfa var mı"
sorusu ancak **içerik doğrulamasıyla** cevaplanır. 208 üniversite × birkaç yol
× içerik doğrulaması = her biri elle yazılmış yüzlerce kırılgan adaptör.

**Sonuç: kurum-kurum yaklaşımı ana strateji OLAMAZ.** Ancak toplayıcıların
kapsamadığı boşluklar için, tek tek ve gerekçeli yazılır.

---

## 2. Çalışan strateji — TOPLAYICI ÖNCE

Türkiye'de kamu ilanları için **yasal olarak zorunlu merkezî bir portal var.**

> Cumhurbaşkanlığına bağlı/ilgili kuruluşlar, bakanlıklar ve diğer kamu
> kurumları, kendi sitelerinde yayımlamak zorunda oldukları ilanları **ilan
> portalında da yayımlamakla yükümlü.** BİK, **81 ilde** yayımlanan resmî
> ilanların dağıtım ve yayın sürecini **tek merkezden** yönetiyor.
> — Basın İlan Kurumu İlan Portalı Yönetmeliği

Bu yüzden Hatay Büyükşehir Belediyesi'nin ilanı `ilan.gov.tr` beslemesinde
görünüyor (canlı veride teyit edildi). Yani **tek kaynak 81 ilin belediye ve
kurum ilanlarını kapsıyor** — 81 × N site gezmeye gerek yok.

### İl kapsamı olan, doğrulanmış kaynaklar

| # | Kaynak | Kapsam | Erişim | Durum |
|---|---|---|---|---|
| K1 | **ilan.gov.tr** (BİK) | **81 il**, tüm kamu kurumları + belediyeler; personel alımı kategorisi (`ats=5`) | `POST /api/api/services/app/Ad/AdsByFilter`; yanıtta `cityCounts` (il kırılımı) ve `numFound` (25.062) | 🟡 şema doğrulandı, oturum şartı çözülmedi (yol haritası §3.1) |
| K2 | **Kariyer Kapısı** | Merkezî kamu işe alım; sözleşmeli personel, bilişim, ünvan değişikliği | **`https://kariyerkapisi.gov.tr/RSS`** — giriş YOK, 33 ilan, `title`/`category`/`link`/`pubDate` | ✅ **hazır, ilk adaptör bu** |
| K3 | kamuilan.sbb.gov.tr | Resmî arşiv, kurum + yıl bazlı | Sunucu-tarafı HTML (207 KB), `ilanDetay.aspx?kod=…` | 🟡 **il filtresi YOK** — yalnız `ddl_yil`, `ddl_ktg`. Arşiv/doğrulama amaçlı. |
| K4 | Jooble API | Özel sektör, konum alanı dolu | Anahtar var, CI'da çalışıyor | ✅ aktif (309 ilan) |
| K5 | Careerjet API | Özel sektör, konum alanı dolu | Anahtar var, CI'da çalışıyor | ✅ aktif (174 ilan) |

**Bölge/il filtresi bu kaynaklardan besleniyor:** K1'in `cityCounts`'u ve
K4/K5'in konum alanı, `geo.il_ilce_ayikla()` ile il/ilçe/bölgeye çevriliyor
(486 kayıtta 460 çözülüyor).

---

## 3. Boşluklar — toplayıcıların kapsamadıkları

Bunlar kurum-kurum gidilmesi **gerekçeli** olan yerler:

| Boşluk | Neden toplayıcıda yok | Nasıl kapatılır |
|---|---|---|
| **KPSS'siz doğrudan alım yapan kurumlar** (ASELSAN, HAVELSAN, TÜRKSAT, STM, TÜBİTAK, Ziraat Teknoloji) | Resmî ilan zorunluluğu dışında, kendi portallarından alıyorlar | Yol haritası F3.6 — her biri ayrı adaptör, sayıları az (~10) |
| **Vizyoner Genç** | Savunma sanayii ortak portalı, BİK'e girmiyor | F3.5 |
| ~~Akademik kadro~~ | — | ❌ **BOŞLUK DEĞİL** (§6.1): BİK kategori `73`/`8`'de. Ayrı adaptör gereksiz. |
| **Özel sektör il bazlı derinlik** | Jooble/Careerjet büyük şehir ağırlıklı | ATS adaptörleri (F4.3) + OSB firmaları (aşağıda) |
| **OSB firmaları** (organize sanayi bölgeleri) | Bölgesel işveren yoğunluğu, hiçbir toplayıcıda toplu yok | **Yeni iz:** OSBÜK'te OSB listesi var → `https://www.osbuk.org/view/sayilarlaosb/osbliste.php`. İl bazlı sanayi işvereni haritası için başlangıç noktası. |

---

## 4. opencode için keşif yöntemi (yeni kaynak eklerken)

Yeni bir kaynak ailesi değerlendirirken sırayla:

1. **Toplayıcıda var mı?** Önce K1/K2'de o kurumun ilanı görünüyor mu diye bak.
   Görünüyorsa ayrı adaptör YAZMA — mükerrer iş ve mükerrer kayıt olur.
2. **RSS var mı?** `/RSS`, `/rss`, `/feed`, sayfa kaynağında `RssLinkiAl`
   benzeri bağlantı. Kariyer Kapısı böyle bulundu.
3. **Soft-404 tuzağını test et.** Uydurma bir yol iste; 200 dönüyorsa durum
   koduna güvenme, içerik doğrula.
4. **robots.txt'i yol bazında oku** (yol haritası §3.2 "Kapalı Kapılar").
5. Hâlâ yoksa `erisim: yok` yaz, sıradakine geç.

---

## 5. Bu dosyanın sınırı

Burada **birleştirme yok**: şema eşleme, tekilleştirme, kayıt defterine giriş
ve adaptör kodu opencode'un işi (yol haritası F2.3, F3, F4). Bu dosya yalnız
"hangi kapı açık, hangisi kapalı, kanıtı ne" sorusunu cevaplar.

---

## 6. İkinci keşif turu — sonuçlar (2026-09-05)

Dört açık soru da kapandı. Üçü toplayıcı-önce tezini güçlendirdi.

### 6.1 Akademik kadro — ayrı adaptör GEREKMİYOR ✅

`ilan.yok.gov.tr` diye bir adres **yok** (benim uydurmamdı; 8.8.8.8 de çözmedi).
Akademik ilanlar zaten BİK'te, kendi kategorisinde:

- `https://www.ilan.gov.tr/ilan/kategori/73/akademik-personel-alimlari`
- `https://www.ilan.gov.tr/ilan/kategori/8/kamu-akademik-personel`

**Tespit edilen BİK kategori kimlikleri** (adaptör için): `2` personel-alimi,
`8` kamu-akademik-personel, `73` akademik-personel-alimlari. Liste sayfasında
ayrıca `ats=5` = PERSONEL ALIMI süzgeci.
→ Yol haritası F3.3'teki "ilan.yok.gov.tr" görevi **iptal**; K1 adaptörü
kategori 73/8'i de çekince akademik kadro kapsanır.

### 6.2 Sağlık alımları — ayrı adaptör GEREKMİYOR ✅

Sağlık Bakanlığı'nın 15.342 sözleşmeli + 3.658 sürekli işçi alımı hem
`ilan.gov.tr`'de (`/ilan/1761908/kamu-akademik-personel-...`) hem
`kariyerkapisi.gov.tr/IlanDetay?i=...`'da yayımlanmış. İl bazlı kadrolar da
aynı ilan içinde.

⚠️ **Nüans:** *sürekli işçi* başvuruları **İŞKUR üzerinden** alınıyor ve İŞKUR
WAF'lı. Ama **ilan** her iki toplayıcıda görünüyor → biz ilanı listeleriz,
başvuru için kaynağa yönlendiririz (§1 kuralı). Kapsama kaybı yok.

### 6.3 OSB haritası — il bazlı sanayi işvereni iskeleti ✅

`https://www.osbuk.org/view/sayilarlaosb/osbliste.php` — 346 KB, sunucu-tarafı
HTML tablo, **418 OSB**. Sütunlar: `sıra | İL | OSB adı | tür | durum`.

- İl sütunu **418/418** `geo.il_to_bolge()` ile çözülüyor — temiz veri.
- Durum dağılımı: **302 İŞLETMEDE (FAALİYETTE)**, 46 planlama, 42 altyapı,
  28 kamulaştırma.
- Faal 302 OSB **78/81 ilde**, yedi bölgenin hepsinde
  (Marmara 80, Karadeniz 51, Ege 50, İç Anadolu 50, G.Doğu 27, Akdeniz 24,
  D.Anadolu 20). En yoğun: Bursa 17, Kocaeli 14, Ankara/İzmir/Tekirdağ 13.

⚠️ **Satırlarda link YOK** — OSB'lerin kendi siteleri bu tablodan çıkmıyor.
Üye firma listesine ulaşmak için her OSB'nin sitesi ayrıca bulunmalı; yani
bu tablo **işveren haritasının iskeleti**, ilan kaynağı değil.
*Önerilen kullanım:* önce faal OSB'leri il bazlı referans veri olarak tut,
sonra en yoğun 8-10 ilde OSB sitelerinde ilan sayfası var mı diye örneklem yap.

### 6.4 Ticaret/Sanayi Odaları — kaynak DEĞİL ❌

ITO, ATO, İZTO ana sayfalarında iş ilanı/kariyer izi arandı: ITO 0, İZTO 0,
ATO 1 (zayıf). **Bu aile kapatıldı**, düşük değerli.

---

## 7. Güncellenmiş sonuç

İkinci tur, kurum-kurum gitme ihtiyacını daha da azalttı: akademik ve sağlık
alımları da toplayıcılarda. Geriye kalan gerçek boşluk **yalnızca**:

1. KPSS'siz doğrudan alım yapan ~10 kurum (ASELSAN, HAVELSAN, TÜBİTAK…)
2. Vizyoner Genç
3. Özel sektörde il bazlı derinlik (ATS adaptörleri + OSB firmaları)

---

## 8. Üçüncü keşif turu — kurum RSS'leri: HEPSİ YANLIŞ POZİTİF ❌

KPSS'siz alım yapan kurumlarda hızlı bir RSS kazancı var mı diye bakıldı.
`/rss`, `/feed`, `/rss.xml` denendi; ilk bakışta umut verici görünenler
**içerik doğrulamasında elendi.** (Bu, §4'teki soft-404 kuralının işe yaradığı
somut örnek.)

| Kurum | Ham sonuç | Uydurma yol testi | Gerçek durum |
|---|---|---|---|
| kariyer.tubitak.gov.tr | /rss, /feed, /rss.xml **hepsi 200** | uydurma yol da **200** | ❌ soft-404, RSS yok |
| www.vizyonergenc.com | /rss, /feed, /rss.xml **hepsi 200** | uydurma yol da **200** | ❌ soft-404, RSS yok |
| www.aselsan.com | /rss.xml **200** | uydurma yol **404** (dürüst) | ❌ ama `content-type: text/html`, **0 `<item>`** → RSS değil, HTML sayfası |
| kariyer.havelsan.com.tr | üçü de 404 | — | ❌ RSS yok |
| www.stm.com.tr | üçü de 404 | — | ❌ RSS yok |

**Sonuç:** Bu kurumların hiçbirinde RSS yok. F3.5 (Vizyoner Genç) ve F3.6
(kurum portalları) için **kısa yol yok** — her biri için tarayıcı ağ sekmesiyle
JSON API aramak gerekecek (§3 madde 1). Sayıları az (~10) olduğu için
katlanılabilir, ama "RSS bulup hızlı bitiririz" beklentisi kurulmasın.

---

## 9. Dördüncü tur — "tüm şirketlerin kendi siteleri" sorusu

Kullanıcı isteği: tüm Türkiye'deki iş siteleri **+ tüm şirketlerin kendi
siteleri**; gerekirse odalar kurumundan firma listesi çekip tek tek bakmak.
İki yol da denendi.

### 9.1 Odalar / TOBB firma kaydı — şirket evreni var, İLAN yok ⚠️

`sanayi.tobb.org.tr` → `https://sanayi.org.tr/#/sanayi-veri-tabani` yönleniyor
(yeni SPA). Veri tabanı **kapasite raporu** olan firmaları içeriyor: faaliyet
alanı, **il dağılımı**, adres, telefon, çalışan sayısı. Erişim için **ücretsiz
üyelik** isteniyor.

Aramada çıkan eski PHP uçları (`yeni_kod_liste71.php`, `kitap_son2_nace.php`,
`sifre_giris3.php`) **artık çalışmıyor** — dördü de aynı 3645 baytlık SPA
kabuğunu döndürüyor. Bayat arama indeksi.

**Değerlendirme — bu yol ilan kaynağı DEĞİL:**

1. Veri tabanı **firma kaydı**, iş ilanı değil. Tam erişsek bile firma adı,
   adres, çalışan sayısı alırız; ilan almayız.
2. İlana çevirmek için her firmanın sitesini bulup kariyer sayfasını ayrıştırmak
   gerekir. On binlerce kayıtlı firma için ölçeklenmez; KOBİ'lerin çoğunda
   kariyer sayfası **yok**.
3. Üyelik arkasındaki verinin yeniden dağıtımı muhtemelen ToS kısıtlı.

→ **Şirket evreni referansı olarak** değerli olabilir (hangi ilde hangi sektör
yoğun), **ilan kaynağı olarak** değil. F4 fazına alınmadı.

### 9.2 ATS platformları — "kendi sitesi" sorusunun ÇALIŞAN cevabı ✅

Kurumsal şirketlerin kariyer sayfaları neredeyse her zaman bir ATS'e
(Lever / Greenhouse / Workable) bağlı ve bu platformların **herkese açık,
kimlik doğrulamasız JSON API'leri** var:

| Platform | Uç nokta | Test |
|---|---|---|
| **Lever** | `https://api.lever.co/v0/postings/<slug>?mode=json` | ✅ `dreamgames` → **19 ilan** |
| **Greenhouse** | `https://boards-api.greenhouse.io/v1/boards/<slug>/jobs` | ✅ çalışıyor |

Lever kayıt yapısı (Dream Games örneği): `text` (başlık), `categories`
(`commitment: Full-time`, `location: Istanbul`, `team: Marketing`,
`allLocations`), `createdAt`, `descriptionPlain`, `country`, `id`.
Yani **çalışma şekli, konum ve takım hazır geliyor** — şema v2'ye doğrudan
oturuyor.

⚠️ **SLUG ÇAKIŞMASI — yanlış pozitif tuzağı.** `boards-api.greenhouse.io/v1/
boards/insider/jobs` **200 ve 9 ilan** döndürdü ama konumlar *New York* ve
*Singapore* — bu Türk Insider (useinsider.com) değil, aynı adlı **ABD medya
şirketi**. Şirket adını slug sanıp denemek yanlış şirketi çeker.

**Doğru yöntem:** slug TAHMİN ETME. Şirketin gerçek kariyer sayfasını aç,
oradan `jobs.lever.co/<slug>` / `boards.greenhouse.io/<slug>` bağlantısını
**oku**. Ek emniyet: çekilen ilanların konumları Türkiye ile uyuşuyor mu diye
doğrula (`geo.il_to_bolge()` ile), uyuşmuyorsa kaynağı reddet.

→ Yol haritası **F4.2** (ATS tespiti) ve **F4.3** (ATS adaptörü) bu bulguyla
uygulanabilir durumda. Tek adaptör onlarca şirketi çeker.

### 9.3 ATS keşfi — ölçülmüş sonuç ve HAZIR eşleme tablosu

10 Türk şirketinin kariyer sayfası tarandı, HTML'de ATS bağlantısı arandı.
Bulunan slug'lar Lever API'sinde doğrulandı.

**"Slug'ı oku, tahmin etme" kuralı ampirik olarak kanıtlandı:**

| Yöntem | Başarı |
|---|---|
| Kariyer sayfasından **okunan** slug | **3/3** ✅ |
| Şirket adından **tahmin edilen** slug | **0/6** ❌ (getir, peak, papara, jotform, hepsiburada, insider — hepsi geçersiz yanıt) |

**Doğrulanmış eşleme — `is_kaynaklari.yml`'e doğrudan girilebilir:**

| Şirket | Platform | Slug | İlan | Konum dağılımı |
|---|---|---|---|---|
| Trendyol | Lever | `trendyol` | **27** | İstanbul/Maslak 13, Bükreş 4, Kocaeli/Gebze 2, Riyad 1 |
| Dream Games | Lever | `dreamgames` | **19** | İstanbul 18, Londra 1 |
| iyzico | Lever | `iyzico` | **12** | İstanbul 12 |

Tek adaptörle **58 gerçek ilan**. Uç nokta:
`https://api.lever.co/v0/postings/<slug>?mode=json` — kimlik doğrulama yok.

⚠️ **Yabancı konumlar var** (Bükreş, Riyad, Londra). Bu, `il_to_bolge()` ile
konum doğrulamasının neden zorunlu olduğunu gösteriyor: Türkiye dışı ilanlar
ya elenmeli ya da `il/bolge = null` ile işaretlenmeli — sessizce
"Bilinmiyor" bölgesine düşürülmemeli.

**Kariyer sayfası taramasının verimi düşük (2/10).** Getir, Peak, Papara,
Jotform, Hepsiburada, Insider'ın kariyer sayfaları **JS ile üretiliyor**, ATS
bağlantısı ham HTML'de yok. Bunlar için tarayıcı ağ sekmesi gerekir — yani
şirket başına elle iş. **Öneri:** önce ham HTML taramasıyla kolay bulunanları
topla (ucuz), JS'lileri sonraya bırak.

---

## 10. Beşinci tur — Vizyoner Genç ÇÖZÜLDÜ, üstelik F3.6'yı da kapsıyor ✅✅

### 10.1 Site taşınmış

`vizyonergenc.com` → **`savunmakariyer.com`** ("Savunma Kariyer | Savunma Sanayi
İş ve Staj İlanları"). Plandaki eski ad güncellenmeli.

Ham HTML işe yaramaz: ana sayfa 2.266 bayt SPA kabuğu, `/sitemap.xml` ve
`/wp-json` bile `text/html` dönüyor (soft-404). Tarayıcı ağ sekmesiyle
**tam açık bir REST API** bulundu.

### 10.2 Uç noktalar — hepsi `public`, KİMLİK DOĞRULAMASIZ

| Uç nokta | Yöntem | Sonuç |
|---|---|---|
| `/api/career-core/public/jobs` | **POST** `{"page":1,"size":100}` | **24 aktif ilan** |
| `/api/common/public/city` | GET | **81 il** (`id` + `name`) |
| `/api/corporate/public/approved-companies?page=1&size=200` | GET | **343 onaylı firma** |

Tek 401: `/api/user-profile/user/visitor` (kullanıcı profili) — ilan verisi açık.

**Yanıt sarmalayıcı:** `{timestamp, httpStatus, header, message, isSuccess, data}`.
Sayfalama `data`: `{content[], totalElements, totalPages, currentPage, jobStats}`.

**İlan kaydı → şema v2 eşlemesi (doğrudan oturuyor):**

| API alanı | v2 alanı |
|---|---|
| `jobTitle` | `baslik` |
| `companyName` | `kurum` |
| **`jobLocation`** (ör. "Ankara") | `il` → `il_to_bolge()` ile `bolge` |
| `startDate` | `tarih` |
| **`endDate`** | `son_basvuru` |
| `redirectUrl` / `/ilanlar?selectedJob=<id>` | `url` |
| `jobStatus` (`PUBLISHED`), `visible`, `applicable` | süzme için |

Örnek: "ASELSAN Sayısal Tasarım Speed Bootcamp", Aselsan, Ankara,
04.09–21.09.2026.

### 10.3 Bu tek kaynak F3.6'nın çoğunu kapsıyor 🎯

Planda ASELSAN/HAVELSAN/TÜRKSAT/STM/TÜBİTAK için **~10 ayrı adaptör**
yazılacaktı. Gerek yok:

- **Onaylı firma dizininde varlar:** Aselsan (+ Global, Konya, Sivas, Aselsannet),
  BAYKAR Makina, HAVELSAN, Havelsan Teknoloji Radar, ROKETSAN, STM.
- **İlan akışında zaten görünüyorlar:** TUSAŞ 3, TEI 5, Aselsan 1,
  Havelsan Teknoloji Radar 1, MKE 1, FNSS 2, Nurol Teknoloji 2,
  TÜSSAF 5, TEITECH 1, Tomtaş 1, Koluman 1.
- **İl dağılımı geliyor:** Ankara 11, Eskişehir 6, Bursa 5, Kayseri 1, Mersin 1.

→ **F3.5 ve F3.6 tek adaptöre indi.** Yalnız bu dizinde olmayan kurumlar
(ör. TÜBİTAK, Türksat, Ziraat Teknoloji) için ayrıca bakılır.

⚠️ Bu bir **savunma sanayii** portalı; kapsamı sektörel. Genel kamu için K1/K2
gerekli, onun yerine geçmez.

---

**Sıradaki keşif turları** (henüz yapılmadı):

- [ ] Faal 302 OSB'nin en yoğun 8-10 ildeki sitelerinde ilan sayfası örneklemi
- [ ] Vizyoner Genç ve TÜBİTAK SPA'larının JSON API'si (tarayıcı ağ sekmesi;
      RSS olmadığı kesinleşti, doğrudan API aranacak)
