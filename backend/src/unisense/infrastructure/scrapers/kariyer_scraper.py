"""Kariyer ilan toplayıcı v1 — Resmî Gazete günlük sayıları + statik kaynak rehberi.

Hat A (kamu) canlı adaptör:
  Resmî Gazete ana sayfası statiktir ve günün PDF'lerini listeler
  (https://www.resmigazete.gov.tr/eskiler/YYYY/AA/YYYYAAGG-N.pdf).
  Her sayı indirilir, metni çıkarılır ve bilişim/personel-alımı anahtar
  kelimeleri taranır. Kayıt = bir günlük sayı (ilan detayı değil, "bugünkü
  sayıda bilişim ilanı var mı?" sinyali + PDF linkleri).

Neden RG: loginsiz, statik HTML, resmi, günlük. Bilinen sınırlar:
  - kariyerkapisi.gov.tr e-Devlet girişi ister → kazınamaz; statik rehberde
    dış bağlantı olarak yer alır (bkz. kariyer_service._KAYNAKLAR).
  - ilan.gov.tr Angular SPA; /api/services/app/Ad/AdsByFilter botlara 404
    dönüyor → adaptör yazılamadı (bulgu PLAN_KARIYER.md'de).
  - kamuilan.sbb.gov.tr ASP.NET WebForms postback istiyor → adaptör adayı.
  - esube.iskur.gov.tr WAF'lı (bkz. iskur_mbk_scraper).
  - osym.gov.tr erişilemiyor (DEVIR Engeller).

Hat B (özel sektör) canlı adaptörler — API anahtarlı, env'den okunur:
  - Jooble: POST https://tr.jooble.org/api/{JOOBLE_API_KEY} (ülke subdomaini
    şart; global host WAF 403). Anahtar: https://jooble.org/api/about
  - Careerjet: GET http://public.api.careerjet.net/search (HTTP-only;
    Referer header şart). affid: https://www.careerjet.com/partners/
  Anahtar yoksa adaptör sessizce atlanır (hata değil) — Hat A yine yazar.
  Desenler career-ops providers/jooble.mjs + careerjet.mjs'ten alındı.

Kayıt şeması (liste, guard uyumlu):
  {id, hat, kaynak, baslik, kurum, sehir, tarih, url, ozet, detay, ilk_gorulme,
   bolumler: [coklu etiket — cift taraflı: bir ilan birden çok bölüme girer]}

Bölüm etiketleme: başlık+açıklama fold'lanıp BÖLÜM_ANAHTAR ile taranır (LLM yok,
deterministik). Tek platformdan GENİŞ çekim (bölüm-agnostik sorgular) + yerelde
etiketleme: Jooble 4 sorgu×5 sayfa (~20 istek/gün, kota 500), Careerjet
3 sorgu×3 sayfa. Kayıtlar 30 günlük kayan pencerede tutulur (budama _merge'de).

Çıktı: data/processed/kariyer_ilanlar.json (liste)
Kullanım: python -m unisense.infrastructure.scrapers.kariyer_scraper
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import UTC, date, datetime
from pathlib import Path

import fitz  # PyMuPDF
import requests

from unisense.core.text import fold_tr
from unisense.domain.geo import il_to_bolge
from unisense.infrastructure.scrapers._guard import ScrapeGuardError, write_json_guarded
from unisense.infrastructure.scrapers.kariyer_registry import aktifler as _aktif_kaynaklar

RG_HOME = "https://www.resmigazete.gov.tr/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
OUT = Path(__file__).resolve().parents[4] / "data" / "processed" / "kariyer_ilanlar.json"
KOSU_DOSYA = Path(__file__).resolve().parents[4] / "data" / "processed" / "kariyer_kosu.json"


def _defter() -> dict[str, dict]:
    """Kayıt defteri (kod → girdi). Yoksa/kırıksa hata (sessiz başarı yasak)."""
    return {g["kod"]: g for g in _aktif_kaynaklar()}


def _rg_ayar() -> tuple[str, int]:
    g = _defter().get("rg", {})
    return (g.get("url") or RG_HOME,
            int((g.get("params") or {}).get("max_pdf_mb", 64)) * 1024 * 1024)

# RG ve Jooble sunucuları ara sertifikayı göndermiyor; Windows deposu
# önbellekten tamamlıyor ama çıplak OpenSSL/certifi zinciri kuramıyor
# (yerel + CI'da CERTIFICATE_VERIFY_FAILED). Çözüm: herkese açık zincir
# (aralar + kökler, sır değil) repoda paketlenir, oturum bunu kullanır.
_CHAIN = Path(__file__).resolve().parent / "tls_extra_chain.pem"

MAX_PDF_BYTES = 64 * 1024 * 1024   # yedek varsayılan; defter params.max_pdf_mb ezer
REQUEST_TIMEOUT = 60
KIBAR_BEKELEME = 1.0               # PDF araları sn

# Bilişim + mühendis + genel personel alımı sinyalleri (fold'lu eşleşir)
ANAHTAR_KELIMELER = {
    "sozlesmeli_bilisim": ["sözleşmeli bilişim personeli", "bilişim personeli"],
    "muhendis": ["bilgisayar mühendisi", "yazılım mühendisi", "mühendis alımı",
                 "bilişim uzmanı", "çözümleyici", "programcı"],
    "siber_guvenlik": ["siber güvenlik", "bilgi güvenliği"],
    "personel_alimi": ["personel alımı", "sözleşmeli personel", "işçi alımı",
                       "uzman yardımcısı", "memur alımı"],
    "kpss": ["kpss"],
}


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    if _CHAIN.exists():
        s.verify = str(_CHAIN)
    return s


def _gunluk_sayilar(html: str) -> dict[str, list[str]]:
    """Ana sayfadaki PDF linklerinden tarih → pdf listesi çıkarır.

    Örn. .../eskiler/2026/09/20260905-2.pdf → {"2026-09-05": [...]}.
    """
    bulunan: dict[str, list[str]] = {}
    for m in re.finditer(r"https://www\.resmigazete\.gov\.tr/eskiler/(\d{4})/(\d{2})/(\d{8})(-\d+)?\.pdf", html):
        yil, ay, tarih, _sonek = m.group(1), m.group(2), m.group(3), m.group(4)
        gun = f"{tarih[0:4]}-{tarih[4:6]}-{tarih[6:8]}"
        # URL'deki yıl/ay ile dosya adı tutarlı olmalı (çöp link eleme)
        if not (yil == gun[0:4] and ay == gun[5:7]):
            continue
        bulunan.setdefault(gun, [])
        if m.group(0) not in bulunan[gun]:
            bulunan[gun].append(m.group(0))
    return bulunan


def _pdf_metni(session: requests.Session, url: str, limit: int) -> tuple[str, int] | None:
    """PDF'i indirip metnini çıkarır. (metin, sayfa_sayısı) ya da None."""
    r = session.get(url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    if len(r.content) > limit:
        return None
    doc = fitz.open(stream=r.content, filetype="pdf")
    try:
        metin = "\n".join(page.get_text() for page in doc)
        return metin, len(doc)
    finally:
        doc.close()


def _eslesme_say(metin_fold: str) -> dict[str, int]:
    """Her sinyal grubunun metinde kaç kez geçtiği."""
    return {
        grup: sum(metin_fold.count(fold_tr(k)) for k in kelimeler)
        for grup, kelimeler in ANAHTAR_KELIMELER.items()
    }


def _scrape_rg(session: requests.Session) -> list[dict]:
    """Resmî Gazete günlük sayıları (sinyal kayıtları)."""
    kayitlar: list[dict] = []
    rg_url, pdf_limit = _rg_ayar()
    r = session.get(rg_url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    sayilar = _gunluk_sayilar(r.text)
    print(f"  RG ana sayfa: {len(sayilar)} günlük sayı bulundu")
    for gun in sorted(sayilar):
        pdfler = sayilar[gun]
        toplam_eslesme: dict[str, int] = {g: 0 for g in ANAHTAR_KELIMELER}
        toplam_sayfa = 0
        atlanan = 0
        for url in pdfler:
            try:
                sonuc = _pdf_metni(session, url, pdf_limit)
            except Exception as e:
                print(f"  ⚠️ {gun} {url.rsplit('/', 1)[-1]} indirilemedi: {type(e).__name__}")
                atlanan += 1
                continue
            if sonuc is None:
                atlanan += 1
                continue
            metin, sayfa = sonuc
            toplam_sayfa += sayfa
            grup_say = _eslesme_say(fold_tr(metin))
            for g, c in grup_say.items():
                toplam_eslesme[g] += c
            time.sleep(KIBAR_BEKELEME)
        kayitlar.append({
            "id": f"rg:{gun}",
            "hat": "kamu",
            "kaynak": "Resmî Gazete",
            "baslik": f"{gun} Resmî Gazete sayıları ({len(pdfler)} PDF)",
            "kurum": "",
            "sehir": "",
            "tarih": gun,
            "url": f"https://www.resmigazete.gov.tr/eskiler/{gun[0:4]}/{gun[5:7]}/{gun.replace('-', '')}.htm",
            "ozet": "Günlük sayı taraması: bilişim/personel-alımı sinyalleri.",
            "detay": {"pdfler": pdfler, "eslesme": toplam_eslesme,
                      "sayfa": toplam_sayfa, "atlanan_pdf": atlanan},
            "ilk_gorulme": gun,
        })
        top = {g: c for g, c in toplam_eslesme.items() if c}
        print(f"  {gun}: {len(pdfler)} pdf, {toplam_sayfa} sayfa, sinyal={top or '-'}")
    return kayitlar


def scrape() -> tuple[list[dict], dict[str, str]]:
    """Tüm adaptörler; kısmi başarı normal — her adaptörün hatası kaydedilir.

    Hiçbir adaptör veri üretemezse liste boş döner → main guard ile exit 1.
    """
    session = _session()
    hatalar: dict[str, str] = {}
    try:
        rg = _scrape_rg(session)
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️ rg düştü: {type(e).__name__}: {e}")
        hatalar["rg"] = f"{type(e).__name__}: {e}"
        rg = []
    hatb = _scrape_hatb(session)
    if hatb:
        print(f"  Hat B: {len(hatb)} ilan (jooble+careerjet)")
    try:
        kam = _scrape_kamuilan(session)
    except Exception as e:  # noqa: BLE001 — kısmi başarı normal (§5)
        print(f"  ⚠️ kamuilan düşti: {type(e).__name__}: {e}")
        hatalar["kamuilan"] = f"{type(e).__name__}: {e}"
        kam = []
    try:
        kk = _scrape_kariyerkapisi(session)
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️ kariyerkapisi düştü: {type(e).__name__}: {e}")
        hatalar["kariyerkapisi"] = f"{type(e).__name__}: {e}"
        kk = []
    return rg + hatb + kam + kk, hatalar


# === Hat B: Jooble + Careerjet (API anahtarlı) ===
# Sorgu/sayfa/anahtar adı kayıt defterinden gelir (F0.4); buradaki listeler
# yalnız defter yoksa düşülen yedek varsayılanlardır.

# Geniş çekim: bölüm-agnostik sorgular, etiketleme yerelde yapılır.
_HATB_JOOBLE_SORGULAR = [
    ("mühendis", "Türkiye"),
    ("yazılım", "Türkiye"),
    ("teknik", "Türkiye"),
    ("bilgisayar", "Türkiye"),
]
_HATB_CJ_SORGULAR = ["mühendis", "yazılım", "tekniker"]
_HATB_SAYFA_JOOBLE = 5
_HATB_SAYFA_CJ = 3
SAKLA_GUN = 30  # kayan pencere: daha eskiler _merge'de budanır
_CJ_UC = "http://public.api.careerjet.net/search"  # HTTPS yok (sağlayıcı tarafı)
_CJ_REFERER = os.environ.get("CAREERJET_REFERER", "http://localhost/")


# Bölüm anahtarları ÖNceden fold'lu (ascii) yazılır; metin fold_tr ile eşleşir.
# Kaynak: PDF nitelik kodları (4531/4533/4611) + yaygın mühendislik bölümleri.
BÖLÜM_ANAHTAR: dict[str, list[str]] = {
    "bilgisayar": ["bilgisayar muhendis", "computer engineer", "bilgisayar programc"],
    "yazilim": ["yazilim muhendis", "yazilim gelistir", "software engineer",
                "software developer", "frontend developer", "backend developer",
                "full stack", "mobil uygulama", "ios developer", "android developer"],
    "elektrik_elektronik": ["elektrik", "elektronik", "haberlesme", "telekomunikasyon"],
    "endustri": ["endustri muhendis", "industrial engineer", "uretim muhendis",
                 "uretim planlama", "yalin uretim"],
    "makine": ["makine muhendis", "mechanical engineer", "mekanik bakim", "hvac"],
    "mekatronik": ["mekatronik", "robotik", "otomasyon", "plc", "gomulu sistem", "embedded"],
    "insaat": ["insaat muhendis", "civil engineer", "santiye", "yapi denetim", "statik proje"],
    "yapay_zeka_veri": ["yapay zeka", "machine learning", "veri bilim", "data scientist",
                        "veri analist", "derin ogrenme", "buyuk veri"],
    "siber": ["siber guvenlik", "bilgi guvenligi", "sizma testi", "penetration", "soc analist"],
    "ag_sistem": ["sistem muhendis", "network", "ag yonetim", "devops", "bulut",
                  "cloud engineer", "veritabani", "database", "sistem admin"],
    "tekniker": ["tekniker", "teknisyen"],
    "isletme": ["isletme", "iktisat", "muhasebe", "finans uzman", "bankacilik"],
}


# Çalışma şekli kalıpları (fold'lu). Öncelik: hibrit > online > yuzyuze —
# "haftada 2 gün ofis, gerisi remote" gibi ilanlar hibrit yakalanır.
CALISMA_ONLINE = ["uzaktan", "remote", "home office", "evden calisma", "remotely"]
CALISMA_HIBRIT = ["hibrit", "hybrid"]
CALISMA_YUZYUZE = ["yuzyuze", "yuz yuze", "ofiste calisma", "ofis ortaminda",
                   "yerinde calisma", "sahada calisma"]


def _calisma_sekli(fold_metin: str) -> str:
    if any(a in fold_metin for a in CALISMA_HIBRIT):
        return "hibrit"
    if any(a in fold_metin for a in CALISMA_ONLINE):
        return "online"
    if any(a in fold_metin for a in CALISMA_YUZYUZE):
        return "yuzyuze"
    return "bilinmiyor"


def _bolum_etiketle(fold_metin: str) -> list[str]:
    """Çift taraflı etiket: uyan TÜM bölümler döner (tekil değil)."""
    return [bolum for bolum, anahtarlar in BÖLÜM_ANAHTAR.items()
            if any(a in fold_metin for a in anahtarlar)]


def _temizle_ham(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def _jooble_normalize(job: dict, bugun: str) -> dict | None:
    baslik = (job.get("title") or "").strip()
    link = (job.get("link") or "").strip()
    if not baslik or not link.startswith("http"):
        return None
    jid = str(job.get("id") or hashlib.sha1(link.encode()).hexdigest()[:12])
    ozet = _temizle_ham(job.get("snippet") or "")[:500]
    metin = fold_tr(f"{baslik} {ozet}")
    return {
        "id": f"jooble:{jid}",
        "hat": "ozel",
        "kaynak": "Jooble",
        "baslik": baslik,
        "kurum": (job.get("source") or "").strip(),  # Jooble kaynak panoyu verir, işvereni değil
        "sehir": (job.get("location") or "").strip(),
        "tarih": (job.get("updated") or bugun)[:10],
        "url": link,
        "ozet": ozet,
        "detay": {"maas": (job.get("salary") or "").strip(), "tur": (job.get("type") or "").strip()},
        "ilk_gorulme": bugun,
        "bolumler": _bolum_etiketle(metin),
        "calisma_sekli": _calisma_sekli(metin),
    }


def _careerjet_normalize(job: dict, bugun: str) -> dict | None:
    baslik = (job.get("title") or "").strip()
    link = (job.get("url") or "").strip()
    if not baslik or not link.startswith("http"):
        return None
    ozet = _temizle_ham(job.get("description") or "")[:500]
    metin = fold_tr(f"{baslik} {ozet}")
    return {
        "id": f"careerjet:{hashlib.sha1(link.encode()).hexdigest()[:12]}",
        "hat": "ozel",
        "kaynak": "Careerjet",
        "baslik": baslik,
        "kurum": (job.get("company") or "").strip(),
        "sehir": (job.get("locations") or "").strip(),
        "tarih": (job.get("date") or bugun)[:10],
        "url": link,
        "ozet": ozet,
        "detay": {"maas": (job.get("salary") or "").strip(), "site": (job.get("site") or "").strip()},
        "ilk_gorulme": bugun,
        "bolumler": _bolum_etiketle(metin),
        "calisma_sekli": _calisma_sekli(metin),
    }


def _scrape_hatb(session: requests.Session) -> list[dict]:
    """Jooble + Careerjet sorguları. Anahtar yoksa [] döner (atlama, hata değil)."""
    kayitlar: list[dict] = []
    bugun = date.today().isoformat()
    defter = _defter()
    jooble_key = os.environ.get(
        (defter.get("jooble") or {}).get("env_key", "JOOBLE_API_KEY"), "").strip()
    if jooble_key:
        sorgular = (defter.get("jooble") or {}).get("sorgular") or _HATB_JOOBLE_SORGULAR
        sayfa_n = int((defter.get("jooble") or {}).get("sayfa", _HATB_SAYFA_JOOBLE))
        for soru in sorgular:
            keywords, location = (soru["keywords"], soru.get("location", "")) \
                if isinstance(soru, dict) else (soru, "Türkiye")
            for page in range(1, sayfa_n + 1):
                try:
                    r = session.post(f"https://tr.jooble.org/api/{jooble_key}",
                                     json={"keywords": keywords, "location": location, "page": page},
                                     timeout=REQUEST_TIMEOUT)
                    r.raise_for_status()
                    jobs = r.json().get("jobs") or []
                except Exception as e:
                    print(f"  ⚠️ jooble '{keywords}' s.{page}: {type(e).__name__}")
                    break
                if not jobs:
                    break
                for j in jobs:
                    k = _jooble_normalize(j, bugun)
                    if k:
                        kayitlar.append(k)
                print(f"  jooble '{keywords}' s.{page}: {len(jobs)} ilan")
                time.sleep(KIBAR_BEKELEME)
    else:
        print("  ○ JOOBLE_API_KEY yok — Jooble atlandı")
    cj_affid = os.environ.get(
        (defter.get("careerjet") or {}).get("env_key", "CAREERJET_API_KEY"), "").strip()
    if cj_affid:
        cj_sorgular = (defter.get("careerjet") or {}).get("sorgular") or _HATB_CJ_SORGULAR
        cj_sayfa = int((defter.get("careerjet") or {}).get("sayfa", _HATB_SAYFA_CJ))
        for keywords in cj_sorgular:
            for page in range(1, cj_sayfa + 1):
                try:
                    r = session.get(_CJ_UC, params={
                        "locale_code": "tr_TR", "keywords": keywords, "location": "",
                        "affid": cj_affid, "user_ip": "127.0.0.1",
                        "user_agent": HEADERS["User-Agent"],
                        "page": page, "pagesize": 50,
                    }, headers={"Referer": _CJ_REFERER}, timeout=REQUEST_TIMEOUT)
                    r.raise_for_status()
                    data = r.json()
                except Exception as e:
                    print(f"  ⚠️ careerjet '{keywords}' s.{page}: {type(e).__name__}")
                    break
                if not isinstance(data, dict) or data.get("type") != "JOBS":
                    print(f"  ⚠️ careerjet '{keywords}' s.{page}: beklenmeyen yanıt")
                    break
                jobs = data.get("jobs") or []
                if not jobs:
                    break
                for j in jobs:
                    k = _careerjet_normalize(j, bugun)
                    if k:
                        kayitlar.append(k)
                print(f"  careerjet '{keywords}' s.{page}: {len(jobs)} ilan")
                time.sleep(KIBAR_BEKELEME)
    else:
        print("  ○ CAREERJET_API_KEY yok — Careerjet atlandı")
    # Aynı link iki sorguda da çıkabilir → id ile tekille
    tekil = list({k["id"]: k for k in kayitlar}.values())
    return tekil


# === Şema v2 (yol haritası §1) ===
# v1 alanları korunur; yeniler eksikse bilinmiyor/null dolar. id v2 formatı
# "kaynak:anahtar" — eski "kaynak-anahtar" id'ler _migrate'te deterministik
# çevrilir (süreklilik korunur, ilk_gorulme sıfırlanmaz).
KAYNAK_KOD = {"Jooble": "jooble", "Careerjet": "careerjet", "Resmî Gazete": "rg",
              "kamuilan.sbb.gov.tr": "kamuilan", "Kariyer Kapısı": "kariyerkapisi"}

V2_BILINMIYOR = "bilinmiyor"


def _v2_id(kayit: dict) -> str:
    eski = str(kayit.get("id") or "")
    if ":" in eski:  # zaten v2
        return eski
    kod = KAYNAK_KOD.get(kayit.get("kaynak") or "", "diger")
    anahtar = eski
    for prefix in (f"{kod}-", "jooble-", "cj-", "rg-"):
        if eski.startswith(prefix):
            anahtar = eski[len(prefix):]
            break
    if kod == "diger":
        kod = {"jooble": "jooble", "cj": "careerjet", "rg": "rg"}.get(
            eski.split("-")[0], "diger")
    return f"{kod}:{anahtar}" if anahtar else eski


def v2_kayit(kayit: dict) -> dict:
    """Eski kaydı v2 şemasına taşır (kayıpsız; eksikler bilinmiyor/null)."""
    k = dict(kayit)
    k["id"] = _v2_id(k)
    k["kaynak_kod"] = KAYNAK_KOD.get(k.get("kaynak") or "", "diger")
    il = (k.get("il") or k.get("sehir") or "").strip()
    k["il"] = il
    k["ilce"] = (k.get("ilce") or "").strip()
    k["bolge"] = il_to_bolge(il) if il else "Bilinmiyor"
    if not k.get("calisma_sekli") or k.get("calisma_sekli") == V2_BILINMIYOR:
        # Eski kayıtlardaki başlık+özetten geriye dönük çıkarım
        k["calisma_sekli"] = _calisma_sekli(
            fold_tr(f"{k.get('baslik', '')} {k.get('ozet', '')}"))
    k.setdefault("istihdam_turu", V2_BILINMIYOR)
    k.setdefault("deneyim", V2_BILINMIYOR)
    k.setdefault("pozisyon_etiket", [])
    k.setdefault("kpss", None)
    k.setdefault("maas", None)
    k.setdefault("son_basvuru", None)
    if k.get("ozet") and len(k["ozet"]) > 300:
        k["ozet"] = k["ozet"][:300]
    return k


def _migrate(kayitlar: list[dict]) -> list[dict]:
    return [v2_kayit(k) for k in kayitlar]


def _anahtar(k: dict) -> str | None:
    """Çapraz-kaynak eşleşme anahtarı: (başlık, kurum, il) fold'lu.

    Başlık veya kurum boşsa None → tekilleştirilmez (yanlış birleşme yok).
    """
    b = fold_tr(k.get("baslik") or "").strip()
    ku = fold_tr(k.get("kurum") or "").strip()
    il = fold_tr(k.get("il") or "").strip()
    if not b or not ku:
        return None
    return f"{b}|{ku}|{il}"


def _dedup_capraz(kayitlar: list[dict]) -> tuple[list[dict], int]:
    """Aynı ilan farklı kaynaklardaysa tekilleştir (saf).

    Kazanan: kamu hattı önce; eşitlikte ilk_gorulme eski olan. Kaybedenin
    bölüm etiketleri kazananla birleştirilir (bilgi kaybı yok).
    Döner: (tekil liste, birleşen sayısı).
    """
    gruplar: dict[str, list[dict]] = {}
    tekiller: list[dict] = []
    for k in kayitlar:
        a = _anahtar(k)
        if a is None:
            tekiller.append(k)
        else:
            gruplar.setdefault(a, []).append(k)
    birlesen = 0
    for grup in gruplar.values():
        if len(grup) == 1:
            tekiller.append(grup[0])
            continue
        sirali = sorted(grup, key=lambda x: (
            0 if x.get("hat") == "kamu" else 1, x.get("ilk_gorulme", "")))
        kazanan = dict(sirali[0])
        etiketler: list[str] = list(kazanan.get("bolumler") or [])
        ilkler = [d.get("ilk_gorulme", "") for d in sirali if d.get("ilk_gorulme")]
        for diger in sirali[1:]:
            for b in diger.get("bolumler") or []:
                if b not in etiketler:
                    etiketler.append(b)
            birlesen += 1
        kazanan["bolumler"] = etiketler
        if ilkler:
            kazanan["ilk_gorulme"] = min(ilkler)  # ilk görülme korunur
        tekiller.append(kazanan)
    return tekiller, birlesen


# === Hat A2: kamuilan.sbb.gov.tr (WebForms postback) ===
# Ana sayfadaki boş arama postback'i güncel ilanları timeline olarak döner:
# ul#nav2 > li > time(h4 gün, h3 ay) + a[href=ilanDetay.aspx?kod=..] >
# p.alt_p1 (kurum) + p.alt_p2 (başlık + em içinde "4 Eylül - 21 Eylül").
TR_AYLAR = {"ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5,
            "haziran": 6, "temmuz": 7, "agustos": 8, "eylul": 9,
            "ekim": 10, "kasim": 11, "aralik": 12}
KAMUILAN_URL = "https://kamuilan.sbb.gov.tr/"


def _tr_tarih(gun: str, ay: str, bugun: date) -> str:
    ay_no = TR_AYLAR.get(fold_tr(ay.strip()), 0)
    try:
        gun_no = int(re.search(r"\d+", gun).group())
    except (AttributeError, ValueError):
        return ""
    if not ay_no or not gun_no:
        return ""
    yil = bugun.year
    try:
        d = date(yil, ay_no, min(gun_no, 28))
    except ValueError:
        return ""
    if (bugun - d).days > 60:  # geçen yılın son ayları bu yıla sarkmış
        try:
            d = date(yil + 1, ay_no, min(gun_no, 28))
        except ValueError:
            return ""
    return d.isoformat()


def _kamuilan_hidden(html: str, name: str) -> str:
    m = re.search('id="' + name + '" value="([^"]*)"', html)
    return m.group(1) if m else ""


def _scrape_kamuilan(session: requests.Session) -> list[dict]:
    """Güncel kamu ilanları (postback + timeline parse)."""
    h = session.get(KAMUILAN_URL, timeout=REQUEST_TIMEOUT).text
    data = {
        "__VIEWSTATE": _kamuilan_hidden(h, "__VIEWSTATE"),
        "__VIEWSTATEGENERATOR": _kamuilan_hidden(h, "__VIEWSTATEGENERATOR"),
        "__EVENTVALIDATION": _kamuilan_hidden(h, "__EVENTVALIDATION"),
        "txb_ara": "",
        "bt_ara": "ARA",
    }
    t = session.post(KAMUILAN_URL, data=data, timeout=REQUEST_TIMEOUT * 2).text
    kayitlar: list[dict] = []
    bugun = date.today().isoformat()
    bugun_d = date.today()
    # Timeline tarih-grupludur: bir <li> = bir gün, içinde birden çok ilan.
    gruplar = re.findall(r"<li>(.*?)</li>\s*(?:<li>|</ul>)", t, re.S)
    for li in gruplar:
        tm = re.search(r"<time[^>]*><h4>(.*?)</h4><h3>(.*?)</h3></time>", li, re.S)
        gun = re.sub(r"<[^>]+>", "", tm.group(1)).strip() if tm else ""
        ay = re.sub(r"<[^>]+>", "", tm.group(2)).strip() if tm else ""
        for m in re.finditer(
                r"<a\s+href='(ilanDetay\.aspx\?kod=[^']+)'[^>]*>.*?"
                r"<p class='alt_p1'>(.*?)</p>.*?"
                r"<p class='alt_p2'>(.*?)<em[^>]*>(.*?)</em>",
                li, re.S):
            link, kurum_h, baslik_h, em_h = m.groups()
            b = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", baslik_h)).strip()
            k = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", kurum_h)).strip()
            if not (b and k):
                continue
            son_basvuru = ""
            parca = re.sub(r"[()]", "", em_h).split("-")
            if len(parca) == 2 and parca[1].strip().split():
                bit = parca[1].strip().split()
                son_basvuru = _tr_tarih(bit[-2] if len(bit) >= 2 else "", bit[-1], bugun_d)
            metin = fold_tr(f"{b} {k}")
            kayitlar.append({
                "id": f"kamuilan:{link.split('kod=')[1][:24]}",
                "hat": "kamu",
                "kaynak": "kamuilan.sbb.gov.tr",
                "kaynak_kod": "kamuilan",
                "baslik": b,
                "kurum": k,
                "il": "",
                "ilce": "",
                "bolge": "Bilinmiyor",
                "tarih": _tr_tarih(gun, ay, bugun_d),
                "son_basvuru": son_basvuru or None,
                "url": (KAMUILAN_URL + link).replace(" ", "%20"),
                "ozet": b[:300],
                "detay": {},
                "ilk_gorulme": bugun,
                "bolumler": _bolum_etiketle(metin),
                "calisma_sekli": _calisma_sekli(metin),
                "istihdam_turu": V2_BILINMIYOR,
                "deneyim": V2_BILINMIYOR,
                "pozisyon_etiket": [],
                "kpss": None,
                "maas": None,
            })
    print(f"  kamuilan: {len(kayitlar)} ilan")
    return kayitlar


def _kosu_raporu(yeni: list[dict], eski_idler: set[str],
                 hatalar: dict[str, str], bugun: str) -> dict:
    """Kaynak bazlı koşu raporu (saf): {kod: {cekilen, yeni, hata}}."""
    cekilen: dict[str, int] = {}
    yeniler: dict[str, int] = {}
    for k in yeni:
        kod = k.get("kaynak_kod") or KAYNAK_KOD.get(k.get("kaynak") or "", "diger")
        cekilen[kod] = cekilen.get(kod, 0) + 1
        if k.get("id") not in eski_idler:
            yeniler[kod] = yeniler.get(kod, 0) + 1
    rapor = {}
    for kod in sorted(set(cekilen) | set(hatalar)):
        rapor[kod] = {"cekilen": cekilen.get(kod, 0),
                      "yeni": yeniler.get(kod, 0),
                      "hata": hatalar.get(kod, "")}
    return {"tarih": bugun, "kaynaklar": rapor}


GECMIS_UZUNLUK = 10
OLU_KOSU_SAYISI = 3  # üst üste bu kadar 0 çekiş = alarm


def _gecmis_guncelle(kosu_dosya: Path, bugun: str, cekilen: dict[str, int]) -> tuple[list[dict], list[str]]:
    """Koşu geçmişine bugünü ekler (aynı gün tekrar koşarsa üzerine yazar).

    Döner: (son N koşu, alarm veren kaynaklar — son 3 koşuda hep 0 çekenler).
    Dosya yoksa/bozuksa boş geçmişten başlar (sessizce, alarm üretmez).
    """
    gecmis: list[dict] = []
    try:
        if kosu_dosya.exists():
            data = json.loads(kosu_dosya.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("gecmis"), list):
                gecmis = [g for g in data["gecmis"]
                          if isinstance(g, dict) and g.get("tarih") != bugun]
    except (json.JSONDecodeError, OSError):
        gecmis = []
    gecmis.append({"tarih": bugun, "cekilen": cekilen})
    gecmis = gecmis[-GECMIS_UZUNLUK:]
    alarmlar: list[str] = []
    if len(gecmis) >= OLU_KOSU_SAYISI:
        son3 = gecmis[-OLU_KOSU_SAYISI:]
        kodlar = {kod for g in son3 for kod in (g.get("cekilen") or {})}
        for kod in sorted(kodlar):
            if all((g.get("cekilen") or {}).get(kod, 0) == 0 for g in son3):
                alarmlar.append(kod)
    return gecmis, alarmlar


# === Hat A1: Kariyer Kapısı RSS (girişsiz, yapılandırılmış) ===
# https://kariyerkapisi.gov.tr/RSS — guid/link/category/title/pubDate.
# category → istihdam türü; "KURUM - başlık" kalıbından kurum ayrışır.
KK_RSS_URL = "https://kariyerkapisi.gov.tr/RSS"
KK_ISTIHDAM = {"sözleşmeli": "sozlesmeli", "staj": "staj", "işçi": "tam_zamanli"}


def _kk_istihdam(category: str) -> str:
    f = fold_tr(category)
    for anahtar, tur in KK_ISTIHDAM.items():
        if fold_tr(anahtar) in f:
            return tur
    return V2_BILINMIYOR


def _scrape_kariyerkapisi(session: requests.Session) -> list[dict]:
    import xml.etree.ElementTree as ET
    from email.utils import parsedate_to_datetime
    kayitlar: list[dict] = []
    bugun = date.today().isoformat()
    r = session.get(KK_RSS_URL, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    kok = ET.fromstring(r.content)
    for item in kok.iter("item"):
        def metin(etiket: str) -> str:
            el = item.find(etiket)
            return (el.text or "").strip() if el is not None else ""
        baslik = metin("title")
        link = metin("link") or metin("guid")
        if not baslik or not link:
            continue
        kurum, _, _kisa = baslik.partition(" - ")
        try:
            tarih = parsedate_to_datetime(metin("pubDate")).date().isoformat()
        except (ValueError, TypeError):
            tarih = ""
        category = metin("category")
        metin_fold = fold_tr(f"{baslik} {category}")
        anahtar = re.search(r"[?&]i=([0-9a-f-]{8,})", link)
        kayitlar.append({
            "id": f"kariyerkapisi:{anahtar.group(1)[:24] if anahtar else hashlib.sha1(link.encode()).hexdigest()[:12]}",
            "hat": "kamu",
            "kaynak": "Kariyer Kapısı",
            "kaynak_kod": "kariyerkapisi",
            "baslik": baslik,
            "kurum": kurum.strip() or baslik,
            "il": "",
            "ilce": "",
            "bolge": "Bilinmiyor",
            "tarih": tarih,
            "son_basvuru": None,
            "url": link,
            "ozet": f"{category} — {baslik}"[:300],
            "detay": {"kategori": category},
            "ilk_gorulme": bugun,
            "bolumler": _bolum_etiketle(metin_fold),
            "calisma_sekli": _calisma_sekli(metin_fold),
            "istihdam_turu": _kk_istihdam(category),
            "deneyim": V2_BILINMIYOR,
            "pozisyon_etiket": [],
            "kpss": None,
            "maas": None,
        })
    print(f"  kariyerkapisi: {len(kayitlar)} ilan")
    return kayitlar


def _merge(yeni: list[dict], eski: list[dict]) -> list[dict]:
    """id'ye göre birleştir: eski kaydın ilk_gorulme'si korunur, gerisi güncellenir.

    30 günlük kayan pencere: tarihi (yoksa ilk_gorulme'si) SAKLA_GUN'den eski
    kayıtlar budanır — dosya şişmez, guard tabanı güncel kalır. Tarihsiz kayıt
    cezalandırılmaz (her zaman korunur).
    """
    bugun = date.today()
    eski_map = {_v2_id(x): x for x in eski if x.get("id")}
    birlesik: list[dict] = []
    budanan = 0
    for k in yeni:
        onceki = eski_map.get(_v2_id(k))
        if onceki and onceki.get("ilk_gorulme"):
            k = {**k, "ilk_gorulme": onceki["ilk_gorulme"]}
        ref = (k.get("tarih") or k.get("ilk_gorulme") or "")[:10]
        try:
            yas = (bugun - date.fromisoformat(ref)).days if ref else 0
        except ValueError:
            yas = 0
        if yas > SAKLA_GUN:
            budanan += 1
            continue
        birlesik.append(k)
    if budanan:
        print(f"  ✂ {budanan} kayıt 30 günden eski — budandı")
    return birlesik


def main() -> None:
    if sys.platform == "win32":
        # Konsol UTF-8 değilse Türkçe karakterler kırılır. BİLEREK main() içinde:
        # modül import'unda stdout değiştirmek pytest capture'ı bozuyordu.
        import io as _io
        sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    try:
        yeni, hatalar = scrape()
    except Exception as e:
        print(f"\n⛔ scrape çöktü ({type(e).__name__}: {e}) — {OUT.name} GÜNCELLENMEDİ")
        sys.exit(1)
    eski: list[dict] = []
    if OUT.exists():
        try:
            data = json.loads(OUT.read_text(encoding="utf-8"))
            eski = data if isinstance(data, list) else []
        except Exception as e:
            print(f"  ⚠️ mevcut dosya okunamadı: {e}")
    eski_idler = {_v2_id(x) for x in eski if x.get("id")}
    birlesik = _migrate(_merge(yeni, eski))
    birlesik, capraz = _dedup_capraz(birlesik)
    if capraz:
        print(f"  ⇄ {capraz} kayıt çapraz-kaynakta birleşti (kamu öncelikli)")
    bugun_str = date.today().isoformat()
    rapor = _kosu_raporu(yeni, eski_idler, hatalar, bugun_str)
    for kod, satir in rapor["kaynaklar"].items():
        print(f"  ▸ {kod}: çekilen={satir['cekilen']} yeni={satir['yeni']}"
              + (f" HATA={satir['hata']}" if satir["hata"] else ""))
    cekilen_map = {kod: s["cekilen"] for kod, s in rapor["kaynaklar"].items()}
    gecmis, alarmlar = _gecmis_guncelle(KOSU_DOSYA, bugun_str, cekilen_map)
    for kod in alarmlar:
        print(f"  🚨 {kod}: son {OLU_KOSU_SAYISI} koşuda 0 ilan — sessizce ölmüş olabilir!")
    KOSU_DOSYA.write_text(json.dumps(
        {**rapor, "toplam_kayit": len(birlesik), "gecmis": gecmis,
         "alarm": alarmlar}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    from collections import Counter as _Counter
    print(f"  calisma_sekli dagilimi: "
          f"{dict(_Counter(x.get('calisma_sekli', '?') for x in birlesik))}")
    try:
        write_json_guarded(OUT, birlesik, label="kariyer")
    except ScrapeGuardError as e:
        print(f"\n⛔ {e}")
        sys.exit(1)
    print(f"  guncelleme: {datetime.now(UTC).strftime('%Y-%m-%d')} "
          f"| kayit: {len(birlesik)}")


if __name__ == "__main__":
    main()
