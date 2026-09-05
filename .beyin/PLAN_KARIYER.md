# Plan Taslağı — Kariyer Sekmesi (Günlük Otomatik İlanlar)

**Yazan:** opencode (plan; kodlama yok)
**Tarih:** 2026-09-04 22:50
**Durum:** uygulandı (opencode, 2026-09-05 00:46) — scraper + API + workflow + sayfa canlı;
bekleyen: ilk CI koşusu (dispatch) + Hat B site-sorgu fazı
**İstek:** üst menüde "Kariyer" sekmesi; sitelerden ilan kazıyıp getiren,
her gün yeni ilan arayan otomatik sayfa.

> Bu dosya yeni taslaktır; `.beyin/` içindeki mevcut yazılar silinmedi.
> Uygulama kodlaması bugünün kapsamı DIŞI.

## Mevcut altyapı (yeniden kullanılacak desenler)

- Scraper deseni: `backend/src/unisense/infrastructure/scrapers/*_scraper.py`,
  `python -m unisense.infrastructure.scrapers.<ad>` ile çalışır,
  çıktı `backend/data/processed/*.json`.
- Cron deseni: `.github/workflows/kpss-sync.yml` — schedule cron +
  `workflow_dispatch`, idempotent scraper, değişiklik yoksa commit yok,
  push → Render autodeploy.
- **Kritik emsal:** `iskur_mbk_scraper.py:1-15` — esube.iskur.gov.tr botları
  WAF ile reddediyor; o yüzden resmi MEB aynası kullanıldı. Kariyer sitelerinin
  (kariyer.net, secretcv, yenibiris vb.) çoğu da bot korumalı → kaynak seçimi
  planın ilk ve en riskli adımı.
- Üst nav: `frontend/src/App.jsx:136-144` (`navItem` listesi) + SEO haritası
  `App.jsx:20-43` (ROUTE_SEO) + route'lar `frontend/src/main.jsx:52-76`.

## İş maddeleri (taslak)

1. **Kaynak araştırması + kararı (kodlamadan önce, onay gerekli)**
   - Adaylar: İŞKUR açık iş (resmi kanal), kariyer.net, secretcv, yenibiris,
     Eleman.net, LinkedIn dışı RSS/servis verenler.
   - Kriter: bot koruması (WAF/CAPTCHA), kullanım şartları + robots.txt,
     günlük cron'a dayanıklılık, şehir/pozisyon/ilan-tarihi alanları.
   - Çıktı: 1–2 birincil kaynak + 1 yedek; İŞKUR dışı sitelerde gerekirse
     resmi ayna/RSS alternatifi (iskur_mbk_scraper emsali).
2. **Backend — scraper + veri**
   - Yeni: `backend/src/unisense/infrastructure/scrapers/kariyer_scraper.py`
     (idempotent: ilan anahtarı örn. kaynak+ilan-id hash'i; aynı ilan tekrar yazılmaz).
   - Çıktı: `backend/data/processed/kariyer_ilanlar.json`
     (başlık, firma, şehir, tarih, link, kaynak; ham HTML saklanmaz).
   - **KVKK/hukuk notu:** kişisel veri yok, yalnızca herkese açık ilan özeti +
     kaynağa link. Tam metin kopyalanmaz, telif açısından başlık+özet+link.
3. **Backend — API**
   - `GET /api/v1/kariyer/ilanlar` (filtre: şehir, anahtar kelime, sayfalama;
     yalnız okuma, rate-limit mevcut desene uyar).
   - DOKUNMA: mevcut `/api/v1/*` path'leri değişmez (AI_CONTEXT yasağı).
4. **Günlük otomasyon**
   - Yeni workflow `.github/workflows/kariyer-sync.yml` (kpss-sync.yml kopyası):
     `cron: '0 5 * * *'` (her gün sabah) + `workflow_dispatch`.
   - Bekçi kuralı: boş/hatalı sonuçta commit YOK (KPSS `[]` faciası tekrarlanmasın —
     bkz. DEVIR Engeller). `backend/data/` elle commit'lenmez.
5. **Frontend — Kariyer sekmesi + sayfa**
   - Nav'a `Kariyer` öğesi (`App.jsx:136-144`), route `/kariyer` (`main.jsx`),
     SEO girdisi (ROUTE_SEO), sayfa `frontend/src/pages/Kariyer.jsx`.
   - Özellikler (taslak): arama + şehir filtresi, "bugün yeni" rozeti,
     karta tıklayınca kaynak siteye dış link, mobil tek sütun (responsive
     1. adımla uyumlu: full-width shell içinde).
6. **Doğrulama**
   - Scraper yerelde 2 gün üst üste koşar: yeni ilan ekleniyor, eski korunuyor,
     boş sonuçta dosya ezilmiyor.
   - Workflow `workflow_dispatch` ile tetiklenir, yeşil görülür.
   - Sayfa test matriksinde (360px dahil) taşmasız açılır.

## Kapsam dışı (bugün / bu taslakta)

- Kod değişikliği yok (plan günü).
- Kullanıcı başvurusu, hesap bağlama, e-posta bildirimi — istenirse ayrı plan.
- Kaynak siteyle anlaşma/API anahtarı gerektiren işler (araştırmada netleşir).

## Karar bekleyenler

- Hangi siteler? (madde 1 araştırması + kullanıcı onayı)
- İlan kategorisi: genel iş ilanları mı, yeni mezun/staj ağırlıklı mı?
  (UniSense kitlesi → önerim: yeni mezun + staj filtresi varsayılan)
- Günlük saat ve dilim (öneri: 05:00 UTC cron).

---

## Ek — Kaynak envanteri (ekleyen: opencode, 2026-09-04 22:58)

Kullanıcının 21 sayfalık "Lisans Seviyesi Kamu İlanları — Tam Takip Rehberi"
(mesajdaki metin; masaüstünde PDF dosyası bulunamadı — `Desktop/*.pdf` boş)
+ career-ops `portals.yml` TR bölümü işlendi. Sonuç: Kariyer sayfası
**iki hatlı** olacak — kamu hattı (PDF) + özel sektör hattı (career-ops).

### Hat A — Kamu ilanları (PDF rehberinden)

| # | Kaynak | Adres | Not |
|---|--------|-------|-----|
| A1 | Kariyer Kapısı | kariyerkapisi.gov.tr/isealim | En önemli kanal; sözleşmeli bilişim neredeyse tamamı buradan |
| A2 | ÖSYM | osym.gov.tr | Merkezi yerleştirme; Kariyer Kapısı'nda görünmez, ayrı takip |
| A3 | Yetenek Kapısı | yetenekkapisi.org | İş/staj eşleşme; yazılım-mühendislik yoğun |
| A4 | kamuilan.sbb.gov.tr | kamuilan.sbb.gov.tr | Resmî arşiv (kurum+yıl); başvuru buradan alınmaz |
| A5 | ilan.gov.tr | ilan.gov.tr/ilan/.../personel-alimi | BİK resmî toplayıcı; üyelik + kayıtlı arama + bildirim |
| A6 | İŞKUR e-Şube | esube.iskur.gov.tr | Kamu İŞÇİ kadrosu; başvuru penceresi ~5 gün; bot WAF'lı (ayna/RSS gerekli) |
| A7 | Resmî Gazete | resmigazete.gov.tr | A grubu + yedek kanal; RSS iddiası doğrulanmamış |
| A8 | ilan.yok.gov.tr | ilan.yok.gov.tr | Akademik kadro (ALES+YDS, KPSS değil) |
| A9 | Vizyoner Genç | vizyonergenc.com | Savunma sanayii ortak portal (YÜKSEK ÖNCELİK, KPSS'siz) |
| A10 | TÜBİTAK | kariyer.tubitak.gov.tr + BİLGEM + ULAKBİM | Çoğu ilanda KPSS yok |
| A11 | Düzenleyiciler | insankaynaklari.tcmb.gov.tr, bddk.org.tr, spk.gov.tr, sayistay.gov.tr | Kendi portalları; Kariyer Kapısı'nda görünmeyebilir |
| A12 | DDO / USOM / GİB | cbddo.gov.tr, usom.gov.tr, gib.gov.tr | Teknoloji kurumları, kendi duyuruları |
| A13 | Şirket portalları | kariyer.havelsan.com.tr, aselsan.com/tr/kariyer, kariyer.turksat.com.tr, borsaistanbul.com İK, mkk.com.tr, stm.com.tr/tr/kariyer | KPSS'siz doğrudan alım |
| A14 | Banka teknolojileri | ziraatteknoloji.com, vakifkatilim.com.tr | Yıl boyu alım, KPSS yok |
| A15 | Güvenlik/savunma | personeltemin.jandarma.gov.tr, personeltemin.msb.gov.tr, pa.edu.tr, mit.gov.tr | Kendi temin sistemleri |
| A16 | Adalet/TBMM | pgm.adalet.gov.tr, bilgiislem.adalet.gov.tr, tbmm.gov.tr | Kariyer Kapısı'na ek izlenir |
| A17 | Toplayıcılar (resmî değil) | ilan.memurlar.net, kamuis.com.tr, isinolsa.com, kamuilan.net, kamuajans.com, kamupersoneli.net | Hızlı derleme; başvuru öncesi orijinal ilan şart |
| A18 | Sosyal | LinkedIn kurum sayfaları, Telegram/X bilişim hesapları | En hızlı duyuru kanalları |

> ⚠️ **2026-09-05 güncellemesi (Claude Code):** Aşağıdaki listede geçen
> **LinkedIn KULLANILMAYACAK** — `robots.txt`'te `User-agent: *` → `Disallow: /`
> (tüm site) ve ayrıca `User-agent: anthropic-ai` → `Disallow: /`. Kanıt ve
> diğer kısıtlı kaynaklar: `PLAN_KARIYER_YOL_HARITASI.md` §3.2 "KAPALI KAPILAR".
> Adaptör yazmadan önce her kaynağın robots iznini yol bazında doğrula.

### Hat B — Özel sektör TR (career-ops `portals.yml`'den, satır referanslı)

Site-sorgu deseni (`site:` + WebSearch, herkese açık ATS API'si yok — `portals.yml:459`):

- kariyer.net (Backend açık / Frontend kapalı), yenibiris.com, secretcv.com,
  isinolsun.com, eleman.net, tr.indeed.com (Backend + AI/ML), careerjet.com.tr
  (`provider: careerjet`, `locale tr_TR` — `portals.yml:2126`), techcareer.net
  (Backend + AI/Python), kodilan.com, youthall.com + toptalent.co (yeni mezun),
  LinkedIn Turkey (genel + junior sorguları + Apify actor girdisi).
- Konum filtresi Türkiye-öncelikli (`location_filter`, 2026-09-02 notu);
  TR pazar notları (net maaş, yemek kartı, deneme süresi 2 ay) `portals.yml:1627-1633`.

Şirket kariyer sayfaları (~50, websearch yöntemi; doğrulanamayanlar kapalı):
Trendyol, Hepsiburada, Insider, Dream Games, Sahibinden, Garanti BBVA Teknoloji,
Turkcell, Iyzico, Craftgate, Gram/Rollic/Spyke/Bigger/Good Job/Panteon (oyun),
Param/Midas/Colendi/Sipay/Paribu (fintek), Softtech, YK Teknoloji, Jotform,
Segmentify, HotelRunner, Vispera, ASELSAN, HAVELSAN, TUSAŞ, n11, Çiçeksepeti,
Modanisa, Armut, Enuygun, Obilet, Codeway, Turkish Technology, Türk Telekom.
Kapalı (URL doğrulanacak): Getir, Peak, Yemeksepeti, Akbank, Papara, Ace,
Masomo, Intertech, BtcTurk, Logo, Baykar, Roketsan, STM, Vodafone.
Not: "şu an taranabilir tek TR ATS: Getir Lever panosu" (`portals.yml:1625`).

### Revize mimari (iki hat)

- `kariyer_scraper.py` iki modüllü: `kamu_*` (Hat A, öncelik A1/A5/A9 resmi kanallar)
  + `ozel_*` (Hat B, career-ops sorgu deseni).
- Çıktı tek dosya `kariyer_ilanlar.json` + `kaynak_hat: kamu|ozel` alanı;
  API'de `hat` filtresi.
- Öncelik sırası (taslak): A1 Kariyer Kapısı → A9 Vizyoner Genç → A5 ilan.gov.tr →
  Hat B site-sorguları → A17 toplayıcılar (doğrulama amaçlı).
- career-ops'a DOKUNMA: `portals.yml` kullanıcı katmanıdır; sorgu metinleri
  referans alınır, dosya kopyalanmaz. career-ops `.beyin` durumu `bekliyor`
  (henüz oturum çalışmamış) — UniSense tarafı bağımsız ilerler.
