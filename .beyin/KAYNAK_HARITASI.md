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
| **Akademik kadro** | Ayrı mevzuat (ALES/YDS) | F3.3 — `ilan.yok.gov.tr` hostname'i **çözülmedi**, doğru adres bulunmalı |
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

**Sıradaki keşif turları** (henüz yapılmadı):

- [ ] `ilan.yok.gov.tr` doğru hostname (8.8.8.8'de de çözülmedi)
- [ ] OSBÜK OSB listesinden il → OSB → üye firma zinciri çıkarılabilir mi
- [ ] İl Sağlık Müdürlükleri / hastane alımları BİK'te görünüyor mu (örneklem)
- [ ] Ticaret/Sanayi Odalarının kendi iş ilanı sayfaları var mı (örneklem)
