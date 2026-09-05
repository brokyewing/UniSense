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
from email.utils import parsedate_to_datetime
from pathlib import Path

import fitz  # PyMuPDF
import requests

from unisense.core.text import fold_tr
from unisense.domain.geo import il_ilce_ayikla, il_to_bolge, metinden_il_bul
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


def scrape(bilinen: set[str] | None = None,
           detayli: set[str] | None = None,
           hatlar: set[str] | None = None) -> tuple[list[dict], dict[str, str]]:
    """Tüm adaptörler; kısmi başarı normal — her adaptörün hatası kaydedilir.

    bilinen: önceki koşudan id seti (BİK artımlı taraması erken dursun diye).
    detayli: PDF detayı okunmuş kamuilan id'leri (tekrar indirilmez).
    hatlar: çalıştırılacak hatlar ({"kamu", "ozel"} alt kümesi; None = tümü).
      F5.1: cron 2 koşuya bölününce her koşu kendi hattını verir; birleşme
      union olduğu için diğer hattın kayıtları korunur.
    Hiçbir adaptör veri üretemezse liste boş döner → main guard ile exit 1.
    """
    kos = hatlar or {"kamu", "ozel"}
    session = _session()
    hatalar: dict[str, str] = {}
    rg, hatb, kam, kk = [], [], [], []
    ak, bg, sk, tt, at = [], [], [], [], []
    if "kamu" in kos:
        try:
            rg = _scrape_rg(session)
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ rg düştü: {type(e).__name__}: {e}")
            hatalar["rg"] = f"{type(e).__name__}: {e}"
            rg = []
    hatb = _scrape_hatb(session) if "ozel" in kos else []
    if hatb:
        print(f"  Hat B: {len(hatb)} ilan (jooble+careerjet)")
    try:
        kam = _scrape_kamuilan(session, detayli) if "kamu" in kos else []
    except Exception as e:  # noqa: BLE001 — kısmi başarı normal (§5)
        print(f"  ⚠️ kamuilan düşti: {type(e).__name__}: {e}")
        hatalar["kamuilan"] = f"{type(e).__name__}: {e}"
        kam = []
    try:
        kk = _scrape_kariyerkapisi(session) if "kamu" in kos else []
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️ kariyerkapisi düştü: {type(e).__name__}: {e}")
        hatalar["kariyerkapisi"] = f"{type(e).__name__}: {e}"
        kk = []
    try:
        ak = _scrape_akademiktr(session) if "kamu" in kos else []
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️ akademiktr düştü: {type(e).__name__}: {e}")
        hatalar["akademiktr"] = f"{type(e).__name__}: {e}"
        ak = []
    try:
        bg = _scrape_ilangovtr(session, bilinen) if "kamu" in kos else []
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️ ilangovtr düştü: {type(e).__name__}: {e}")
        hatalar["ilangovtr"] = f"{type(e).__name__}: {e}"
        bg = []
    try:
        sk = _scrape_savunmakariyer(session) if "kamu" in kos else []
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️ savunmakariyer düştü: {type(e).__name__}: {e}")
        hatalar["savunmakariyer"] = f"{type(e).__name__}: {e}"
        sk = []
    try:
        tt = _scrape_turksat(session) if "kamu" in kos else []
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️ turksat düştü: {type(e).__name__}: {e}")
        hatalar["turksat"] = f"{type(e).__name__}: {e}"
        tt = []
    try:
        at = _scrape_ats(session) if "ozel" in kos else []
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️ ats düştü: {type(e).__name__}: {e}")
        hatalar["ats"] = f"{type(e).__name__}: {e}"
        at = []
    return rg + hatb + kam + kk + ak + bg + sk + tt + at, hatalar


# === Hat B: Jooble + Careerjet (API anahtarlı) ===
# Sorgu/sayfa/anahtar adı kayıt defterinden gelir (F0.4); buradaki listeler
# yalnız defter yoksa düşülen yedek varsayılanlardır.

# Geniş çekim: bölüm-agnostik sorgular, etiketleme yerelde yapılır.
# F4.1: tüm meslek grupları (mühendislik + sağlık/eğitim/muhasebe/satış/hukuk/lojistik).
_HATB_JOOBLE_SORGULAR = [
    ("mühendis", "Türkiye"),
    ("yazılım", "Türkiye"),
    ("teknik", "Türkiye"),
    ("bilgisayar", "Türkiye"),
    ("sağlık", "Türkiye"),
    ("öğretmen", "Türkiye"),
    ("muhasebe", "Türkiye"),
    ("satış", "Türkiye"),
    ("hukuk", "Türkiye"),
    ("lojistik", "Türkiye"),
]
_HATB_CJ_SORGULAR = ["mühendis", "yazılım", "tekniker", "sağlık",
                     "öğretmen", "muhasebe", "satış"]
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


# KPSS çıkarımı (F3.8): metinde KPSS geçiyor mu + puan türü (P3/P93/P94).
# Yoksa None (bilinmiyor) — uydurma yok. kpss_service ile bağ ileride.
KPSS_TUR_RE = r"\bp\s?(\d{1,3})\b"


def _kpss_bilgi(fold_metin: str) -> tuple[bool | None, str | None]:
    tur = None
    m = re.search(KPSS_TUR_RE, fold_metin)
    if m:
        tur = f"P{m.group(1)}"
    if "kpss" in fold_metin or tur:
        return True, tur
    return None, None


def _bolum_etiketle(fold_metin: str) -> list[str]:
    """Çift taraflı etiket: uyan TÜM bölümler döner (tekil değil)."""
    return [bolum for bolum, anahtarlar in BÖLÜM_ANAHTAR.items()
            if any(a in fold_metin for a in anahtarlar)]


_ISO_TARIH = re.compile(r"^\d{4}-\d{2}-\d{2}")


def _tarih_iso(ham: str | None, bugun: str) -> str:
    """Kaynak tarihini ISO (YYYY-MM-DD) yap.

    Careerjet RFC-822 veriyor ("Wed, 29 Jun 2026 10:00:00 GMT"); buna [:10]
    uygulamak "Wed, 29 Ju" gibi bozuk değer üretiyordu — 228 kaydın tamamı
    böyleydi. Jooble'ın `updated` alanı zaten ISO, o yol korunur.
    """
    ham = (ham or "").strip()
    if not ham:
        return bugun
    if _ISO_TARIH.match(ham):
        return ham[:10]
    try:
        return parsedate_to_datetime(ham).date().isoformat()
    except (TypeError, ValueError):
        return bugun


def _temizle_ham(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


# Jooble `type` alani 744 kayittan 658'inde dolu (%88) — zaten cekiliyordu ama
# istihdam_turu'ne eslenmedigi icin o alan %94 bos gorunuyordu (olcum 2026-09-05).
_JOOBLE_ISTIHDAM = {
    "tam zamanli": "tam_zamanli",
    "yari zamanli": "yari_zamanli",
    "staj": "staj",
    "gecici": "gecici",
    "donemsel": "gecici",
    "sozlesmeli": "sozlesmeli",
}


def _istihdam_turu_metinden(ham: str | None) -> str:
    """Serbest metinden istihdam türü ("Tam zamanlı", "Staj", …).

    Birden çok değer virgülle gelebiliyor ("Tam zamanlı, Yarı zamanlı");
    ilk tanınan alınır. Tanınmazsa `bilinmiyor`.
    """
    if not ham:
        return V2_BILINMIYOR
    for parca in str(ham).split(","):
        anahtar = fold_tr(parca.strip())
        if anahtar in _JOOBLE_ISTIHDAM:
            return _JOOBLE_ISTIHDAM[anahtar]
    return V2_BILINMIYOR


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
        "tarih": _tarih_iso(job.get("updated"), bugun),
        "url": link,
        "ozet": ozet,
        "detay": {"maas": (job.get("salary") or "").strip(), "tur": (job.get("type") or "").strip()},
        "ilk_gorulme": bugun,
        "bolumler": _bolum_etiketle(metin),
        "calisma_sekli": _calisma_sekli(metin),
        "istihdam_turu": _istihdam_turu_metinden(job.get("type")),
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
        "tarih": _tarih_iso(job.get("date"), bugun),
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
              "kamuilan.sbb.gov.tr": "kamuilan", "Kariyer Kapısı": "kariyerkapisi",
              "AkademikTR": "akademiktr", "ilan.gov.tr": "ilangovtr",
              "Savunma Kariyer": "savunmakariyer", "TÜRKSAT Kariyer": "turksat"}

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
    if not k.get("kaynak_kod"):
        k["kaynak_kod"] = KAYNAK_KOD.get(k.get("kaynak") or "", "diger")
    # Konum normalizasyonu. Ham konum tek alanda ve çok biçimli geliyor
    # ("İstanbul", "İSTANBUL", "İstanbul Avrupa", "Ataşehir, İstanbul",
    # "Konak, İzmir", "Istanbul"). Ölçüm 2026-09-05: `il` alanında 355 farklı
    # değer vardı, yalnız İstanbul'un ~95 varyantı. il_ilce_ayikla sırayı
    # önemsemez ve KANONİK il adı döndürür -> 355 değer 65 ile indi.
    ham_konum = (k.get("il") or k.get("sehir") or "").strip()
    il, ilce, bolge = il_ilce_ayikla(ham_konum)
    if not il:
        # Kamu kaynaklarının çoğu şehir alanı vermiyor; il yalnız kurum adında
        # geçiyor ("ARDAHAN ÜNİVERSİTESİ"). 128 ilsiz kaydın 82'si böyle çözülüyor.
        il = metinden_il_bul(k.get("kurum")) or metinden_il_bul(k.get("baslik"))
        bolge = il_to_bolge(il) if il else "Bilinmiyor"
    k["il"] = il or ""
    k["ilce"] = (k.get("ilce") or ilce or "").strip()
    k["bolge"] = bolge
    if not k.get("calisma_sekli") or k.get("calisma_sekli") == V2_BILINMIYOR:
        # Eski kayıtlardaki başlık+özetten geriye dönük çıkarım
        k["calisma_sekli"] = _calisma_sekli(
            fold_tr(f"{k.get('baslik', '')} {k.get('ozet', '')}"))
    if k.get("kpss") is None:
        # F3.8: KPSS şartı + puan türü çıkarımı (yoksa None kalır)
        var_mi, tur = _kpss_bilgi(fold_tr(f"{k.get('baslik', '')} {k.get('ozet', '')}"))
        k["kpss"] = var_mi
        if tur:
            det = dict(k.get("detay") or {})
            det.setdefault("kpss_tur", tur)
            k["detay"] = det
    if not k.get("istihdam_turu") or k["istihdam_turu"] == V2_BILINMIYOR:
        # Geriye dönük: Jooble kayıtlarında tür zaten detay.tur'da duruyor
        k["istihdam_turu"] = _istihdam_turu_metinden((k.get("detay") or {}).get("tur"))
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
# Detay: ilanDetay.aspx İLAN PDF'ini döner (Referer şart; kod KESILMEZ —
# kesik kod 404 verir). PDF metninden KPSS bilgisi çıkarılır.
TR_AYLAR = {"ocak": 1, "subat": 2, "mart": 3, "nisan": 4, "mayis": 5,
            "haziran": 6, "temmuz": 7, "agustos": 8, "eylul": 9,
            "ekim": 10, "kasim": 11, "aralik": 12}
KAMUILAN_URL = "https://kamuilan.sbb.gov.tr/"
KAMUILAN_DETAY_TAVAN = 25  # koşu başına PDF detayı (kibarlık + süre)
KAMUILAN_PDF_TAVAN = 8 * 1024 * 1024


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


def _kamuilan_detay(session: requests.Session, url: str) -> str:
    """İlan PDF'ini indirip metnini çıkarır (boş string de olabilir)."""
    r = session.get(url, headers={"Referer": KAMUILAN_URL},
                    timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    if len(r.content) > KAMUILAN_PDF_TAVAN or not r.content.startswith(b"%PDF"):
        return ""
    doc = fitz.open(stream=r.content, filetype="pdf")
    try:
        return "\n".join(page.get_text() for page in doc)[:20000]
    finally:
        doc.close()


def _scrape_kamuilan(session: requests.Session,
                     detayli: set[str] | None = None) -> list[dict]:
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
    detayli = detayli or set()
    detay_sayac = 0
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
            link_tam = (KAMUILAN_URL + link).replace(" ", "%20")
            rid = f"kamuilan:{hashlib.sha1(link_tam.encode()).hexdigest()[:16]}"
            kpss, kpss_tur, detay_okundu = None, None, False
            if rid not in detayli and detay_sayac < KAMUILAN_DETAY_TAVAN:
                try:
                    dmetin = _kamuilan_detay(session, link_tam)
                    time.sleep(KIBAR_BEKELEME)
                except Exception as e:  # noqa: BLE001
                    print(f"  ⚠️ kamuilan detay: {type(e).__name__}")
                    dmetin = ""
                if dmetin:
                    kpss, kpss_tur = _kpss_bilgi(fold_tr(f"{b} {k} {dmetin}"))
                    detay_okundu = True
                    detay_sayac += 1
            kayitlar.append({
                "id": rid,
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
                "url": link_tam,
                "ozet": b[:300],
                "detay": {"detay_okundu": detay_okundu,
                          **({"kpss_tur": kpss_tur} if kpss_tur else {})},
                "ilk_gorulme": bugun,
                "bolumler": _bolum_etiketle(metin),
                "calisma_sekli": _calisma_sekli(metin),
                "istihdam_turu": V2_BILINMIYOR,
                "deneyim": V2_BILINMIYOR,
                "pozisyon_etiket": [],
                "kpss": kpss,
                "maas": None,
            })
    print(f"  kamuilan: {len(kayitlar)} ilan ({detay_sayac} detay okundu)")
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
    """Koşu geçmişine bugünü ekler.

    Aynı gün tekrar koşarsa (F5.1 bölünmüş kamu/özel koşuları) kayıtlar
    anahtar-bazında birleşir — ikinci koşu birincinin sayımlarını silmez.
    Döner: (son N koşu, alarm veren kaynaklar — son 3 koşuda hep 0 çekenler).
    Dosya yoksa/bozuksa boş geçmişten başlar (sessizce, alarm üretmez).
    """
    gecmis: list[dict] = []
    try:
        if kosu_dosya.exists():
            data = json.loads(kosu_dosya.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("gecmis"), list):
                gecmis = [g for g in data["gecmis"] if isinstance(g, dict)]
    except (json.JSONDecodeError, OSError):
        gecmis = []
    onceki = {**(gecmis[-1].get("cekilen") or {})} if gecmis and gecmis[-1].get("tarih") == bugun else {}
    onceki.update(cekilen)
    gecmis = [g for g in gecmis if g.get("tarih") != bugun]
    gecmis.append({"tarih": bugun, "cekilen": onceki})
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


# === Hat A8: akademiktr.com (akademik kadro; ilan.yok.gov.tr ölü) ===
# ilan.yok.gov.tr çözülmüyor (DNS yok). Yerine özel toplayıcı: kategori
# sayfaları SSR, detay linkleri (/ilan/<slug>-alim-ilani-N) + detayda tarih.
AKADEMIKTR_KATEGORILER = [
    "arastirma-gorevlisi", "ogretim-gorevlisi", "dr-ogretim-uyesi",
    "docent", "profesor",
]
AKADEMIKTR_URL = "https://akademiktr.com"
AKADEMIKTR_DETAY_TAVAN = 300  # koşu başına detay üst sınırı (kibarlık)


def _akademiktr_parse_liste(html: str) -> list[str]:
    linkler = []
    for m in re.finditer(r'href="(/ilan/[^"]+?-alim-ilani-\d+)"', html):
        if m.group(1) not in linkler:
            linkler.append(m.group(1))
    return linkler


def _akademiktr_parse_detay(html: str) -> dict:
    def ilk(desene: str) -> str:
        m = re.search(desene, html, re.S)
        return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
    baslik = ilk(r'<h1 class="detail-title-new">(.*?)</h1>')
    tarihler = re.findall(r"(\d{2})\.(\d{2})\.(\d{4})", html)
    iso = sorted({f"{y}-{m}-{d}" for d, m, y in tarihler})
    return {"baslik": baslik, "tarihler": iso}


def _scrape_akademiktr(session: requests.Session) -> list[dict]:
    kayitlar: list[dict] = []
    bugun = date.today().isoformat()
    gorulen: set[str] = set()
    for kat in AKADEMIKTR_KATEGORILER:
        try:
            h = session.get(f"{AKADEMIKTR_URL}/ilan/{kat}", timeout=REQUEST_TIMEOUT).text
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ akademiktr/{kat}: {type(e).__name__}")
            continue
        for link in _akademiktr_parse_liste(h):
            if link in gorulen or len(kayitlar) >= AKADEMIKTR_DETAY_TAVAN:
                continue
            gorulen.add(link)
            try:
                d = session.get(AKADEMIKTR_URL + link, timeout=REQUEST_TIMEOUT).text
                time.sleep(KIBAR_BEKELEME)
            except Exception as e:  # noqa: BLE001
                print(f"  ⚠️ akademiktr detay: {type(e).__name__}")
                continue
            p = _akademiktr_parse_detay(d)
            if not p["baslik"]:
                continue
            uni = p["baslik"].split(" Öğretim")[0].split(" Araştırma")[0].strip()
            metin = fold_tr(p["baslik"])
            kayitlar.append({
                "id": f"akademiktr:{hashlib.sha1(link.encode()).hexdigest()[:16]}",
                "hat": "kamu",
                "kaynak": "AkademikTR",
                "kaynak_kod": "akademiktr",
                "baslik": p["baslik"],
                "kurum": uni,
                "il": "",
                "ilce": "",
                "bolge": "Bilinmiyor",
                "tarih": p["tarihler"][0] if p["tarihler"] else "",
                "son_basvuru": p["tarihler"][-1] if len(p["tarihler"]) > 1 else None,
                "url": AKADEMIKTR_URL + link,
                "ozet": f"{kat} — {p['baslik']}"[:300],
                "detay": {"kategori": kat},
                "ilk_gorulme": bugun,
                "bolumler": _bolum_etiketle(metin),
                "calisma_sekli": _calisma_sekli(metin),
                "istihdam_turu": V2_BILINMIYOR,
                "deneyim": V2_BILINMIYOR,
                "pozisyon_etiket": [],
                "kpss": None,
                "maas": None,
            })
    print(f"  akademiktr: {len(kayitlar)} ilan")
    return kayitlar


# === Hat K1: ilan.gov.tr BİK API (81 il, personel alımı) ===
# POST /api/api/services/app/Ad/AdsByFilter — kritik detay: sorting "id desc"
# (diğer değerler sessizce 0 döndürür). Sayfa tavanı 20. Süzgeç parametreleri
# yok sayılır → adTypeFilters "PERSONEL ALIMI" yerelde süzülür (~%10).
# Keşif: KAYNAK_HARITASI.md §11 (Claude Code).
ILANGOVTR_UC = "https://www.ilan.gov.tr/api/api/services/app/Ad/AdsByFilter"
ILANGOVTR_SAYFA_TAVAN = 300  # 300×20 = 6000 kayıt; günlük artımlıda erken-durur
ILANGOVTR_ERKEN_BITIS = 2    # üst üste bu kadar sayfada yenilik yoksa dur


def _ilangovtr_personel_mi(ad: dict) -> bool:
    for f in ad.get("adTypeFilters") or []:
        if isinstance(f, dict) and f.get("value") == "PERSONEL ALIMI":
            return True
    return False


def _ilangovtr_normalize(ad: dict, bugun: str) -> dict | None:
    aid = ad.get("id")
    baslik = (ad.get("title") or "").strip()
    if not aid or not baslik:
        return None
    il = (ad.get("addressCityName") or "").strip().upper()
    ilce = (ad.get("addressCountyName") or "").strip()
    kurum = (ad.get("advertiserName") or "").strip()
    url_rel = (ad.get("urlStr") or "").strip()
    url = ("https://www.ilan.gov.tr" + url_rel if url_rel.startswith("/")
           else f"https://www.ilan.gov.tr/ilan/{aid}")
    metin = fold_tr(f"{baslik} {kurum}")
    return {
        "id": f"ilangovtr:{aid}",
        "hat": "kamu",
        "kaynak": "ilan.gov.tr",
        "kaynak_kod": "ilangovtr",
        "baslik": baslik,
        "kurum": kurum,
        "il": il,
        "ilce": ilce,
        "bolge": il_to_bolge(il) if il else "Bilinmiyor",
        "tarih": (ad.get("publishStartDate") or "")[:10],
        "son_basvuru": None,
        "url": url,
        "ozet": f"{ad.get('adNo', '')} — {baslik}"[:300],
        "detay": {"adNo": ad.get("adNo", ""), "adSourceName": ad.get("adSourceName", "")},
        "ilk_gorulme": bugun,
        "bolumler": _bolum_etiketle(metin),
        "calisma_sekli": _calisma_sekli(metin),
        "istihdam_turu": V2_BILINMIYOR,
        "deneyim": V2_BILINMIYOR,
        "pozisyon_etiket": [],
        "kpss": None,
        "maas": None,
    }


def _scrape_ilangovtr(session: requests.Session,
                      bilinen: set[str] | None = None) -> list[dict]:
    """BİK personel ilanları (id desc = en yeni önce).

    Günlük artımlı: üst üste ERKEN_BITIS sayfada yenilik yoksa durur — ilk
    koşuda tavana kadar gider, sonrakiler birkaç sayfada biter. Geriye dönük
    tam tarama için ILANGOVTR_TAM_TARAMA=1 (erken-duruş atlanır).
    """
    tam = bool(os.environ.get("ILANGOVTR_TAM_TARAMA", "").strip())
    kayitlar: list[dict] = []
    bugun = date.today().isoformat()
    gorulen: set[str] = set()
    bilinen = bilinen or set()
    ardarda_tanidik = 0
    for sayfa in range(ILANGOVTR_SAYFA_TAVAN):
        try:
            r = session.post(
                ILANGOVTR_UC,
                json={"skipCount": sayfa * 20, "maxResultCount": 20,
                      "sorting": "id desc"},
                headers={"Referer": "https://www.ilan.gov.tr/",
                         "Origin": "https://www.ilan.gov.tr",
                         "X-Requested-With": "XMLHttpRequest",
                         "Accept": "application/json",
                         "Content-Type": "application/json-patch+json"},
                timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            ads = (r.json().get("result") or {}).get("ads") or []
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ ilangovtr s.{sayfa}: {type(e).__name__}")
            break
        if not ads:
            break
        yeni_sayfa = 0
        sayfa_yeni_id = 0
        for ad in ads:
            if not _ilangovtr_personel_mi(ad):
                continue
            k = _ilangovtr_normalize(ad, bugun)
            if k and k["id"] not in gorulen:
                gorulen.add(k["id"])
                kayitlar.append(k)
                yeni_sayfa += 1
                if k["id"] not in bilinen:
                    sayfa_yeni_id += 1
        print(f"  ilangovtr s.{sayfa}: {yeni_sayfa} personel ({len(ads)} kayıt)")
        time.sleep(KIBAR_BEKELEME)
        if sayfa_yeni_id == 0:
            ardarda_tanidik += 1
            if not tam and ardarda_tanidik >= ILANGOVTR_ERKEN_BITIS:
                print(f"  ilangovtr: {ILANGOVTR_ERKEN_BITIS} sayfadır yenilik yok — erken duruş")
                break
        else:
            ardarda_tanidik = 0
    print(f"  ilangovtr: {len(kayitlar)} personel ilanı")
    return kayitlar


# === Hat A9: savunmakariyer.com (eski Vizyoner Genç) ===
# Vite SPA; herkese açık API bulundu (JS paketinden): POST
# /api/career-core/public/jobs {page, size, sortDirection}. Auth yok.
# jobType: FULL_TIME|PART_TIME|INTERNSHIP|SCHOLARSHIP alınır, ACTIVITY
# (etkinlik) atlanır. Detay: /ilanlar/ilanDetay/{id}.
SK_UC = "https://savunmakariyer.com/api/career-core/public/jobs"
SK_ISTIHDAM = {"FULL_TIME": "tam_zamanli", "PART_TIME": "yari_zamanli",
               "INTERNSHIP": "staj"}


def _scrape_savunmakariyer(session: requests.Session) -> list[dict]:
    kayitlar: list[dict] = []
    bugun = date.today().isoformat()
    sayfa, toplam_sayfa = 1, 1
    while sayfa <= toplam_sayfa:
        try:
            r = session.post(
                SK_UC, json={"page": sayfa, "size": 25, "sortDirection": "DESC"},
                headers={"Origin": "https://savunmakariyer.com",
                         "Referer": "https://savunmakariyer.com/ilanlar"},
                timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            data = r.json().get("data") or {}
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ savunmakariyer s.{sayfa}: {type(e).__name__}")
            break
        toplam_sayfa = int(data.get("totalPages") or 1)
        ads = data.get("content") or []
        if not ads:
            break
        for ad in ads:
            if not isinstance(ad, dict) or ad.get("jobType") == "ACTIVITY":
                continue
            jid = str(ad.get("id") or "").strip()
            baslik = (ad.get("jobTitle") or "").strip()
            if not jid or not baslik:
                continue
            kurum = (ad.get("companyName") or "").strip()
            sehir = (ad.get("jobLocation") or "").strip()
            ozet = _temizle_ham(ad.get("jobDescription") or "")[:300]
            metin = fold_tr(f"{baslik} {kurum} {ozet}")
            kayitlar.append({
                "id": f"savunmakariyer:{jid[:24]}",
                "hat": "kamu",
                "kaynak": "Savunma Kariyer",
                "kaynak_kod": "savunmakariyer",
                "baslik": baslik,
                "kurum": kurum,
                "il": sehir,
                "ilce": "",
                "bolge": il_to_bolge(sehir) if sehir else "Bilinmiyor",
                "tarih": (ad.get("startDate") or ad.get("createdAt") or "")[:10],
                "son_basvuru": (ad.get("endDate") or "")[:10] or None,
                "url": f"https://savunmakariyer.com/ilanlar/ilanDetay/{jid}",
                "ozet": ozet,
                "detay": {"jobType": ad.get("jobType", ""),
                          "basvuru_sayisi": ad.get("applicationCount")},
                "ilk_gorulme": bugun,
                "bolumler": _bolum_etiketle(metin),
                "calisma_sekli": _calisma_sekli(metin),
                "istihdam_turu": SK_ISTIHDAM.get(ad.get("jobType") or "", V2_BILINMIYOR),
                "deneyim": V2_BILINMIYOR,
                "pozisyon_etiket": [],
                "kpss": False,  # savunma şirketleri kendi alımını yapar
                "maas": None,
            })
        print(f"  savunmakariyer s.{sayfa}: {len(ads)} kayıt")
        time.sleep(KIBAR_BEKELEME)
        sayfa += 1
    print(f"  savunmakariyer: {len(kayitlar)} ilan")
    return kayitlar


# === Hat A13: TÜRKSAT kariyer (SSR tablo; şu an 0 açık pozisyon) ===
# https://kariyer.turksat.com.tr/jobs — table.G satırları; boşken "no-record"
# mesajı döner. Yapı hazır, ilan çıkınca otomatik akar.
TURKSAT_JOBS_URL = "https://kariyer.turksat.com.tr/jobs"


def _scrape_turksat(session: requests.Session) -> list[dict]:
    kayitlar: list[dict] = []
    bugun = date.today().isoformat()
    h = session.get(TURKSAT_JOBS_URL, timeout=REQUEST_TIMEOUT).text
    if "no-record" in h:
        print("  turksat: açık pozisyon yok")
        return []
    for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", h, re.S):
        satir = m.group(1)
        link = re.search(r'href="(/jobs?/[^"]+|/job[^"]+|/ilan[^"]+)"', satir)
        metin = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", satir)).strip()
        if len(metin) < 10:
            continue
        url = ("https://kariyer.turksat.com.tr" + link.group(1)
               if link else TURKSAT_JOBS_URL)
        fold = fold_tr(metin)
        kayitlar.append({
            "id": f"turksat:{hashlib.sha1((url + metin[:80]).encode()).hexdigest()[:16]}",
            "hat": "kamu",
            "kaynak": "TÜRKSAT Kariyer",
            "kaynak_kod": "turksat",
            "baslik": metin[:200],
            "kurum": "TÜRKSAT",
            "il": "",
            "ilce": "",
            "bolge": "Bilinmiyor",
            "tarih": bugun,
            "son_basvuru": None,
            "url": url,
            "ozet": metin[:300],
            "detay": {},
            "ilk_gorulme": bugun,
            "bolumler": _bolum_etiketle(fold),
            "calisma_sekli": _calisma_sekli(fold),
            "istihdam_turu": V2_BILINMIYOR,
            "deneyim": V2_BILINMIYOR,
            "pozisyon_etiket": [],
            "kpss": False,  # KPSS'siz doğrudan alım (rehber bulgusu)
            "maas": None,
        })
    print(f"  turksat: {len(kayitlar)} ilan")
    return kayitlar


# === Hat F4.3: şirket ATS panoları (defterdeki sirket_ats'ten beslenir) ===
# Lever: GET api.lever.co/v0/postings/{slug}?mode=json (auth yok).
# Ashby: GET api.ashbyhq.com/posting-api/job-board/{slug} (auth yok).
# workplaceType doğrudan çalışma şekli verir (Onsite/Remote/Hybrid).
ATS_CALISMA = {"onsite": "yuzyuze", "remote": "online", "hybrid": "hibrit"}


def _ats_calisma(workplace: str | None, metin_fold: str) -> str:
    if workplace:
        w = ATS_CALISMA.get(workplace.strip().lower())
        if w:
            return w
    return _calisma_sekli(metin_fold)


def _ats_kayit(*, kaynak_id: str, kaynak_ad: str, sirket: str, baslik: str,
               sehir: str, tarih: str, url: str, ozet: str, workplace: str | None,
               bugun: str, ek_detay: dict | None = None) -> dict | None:
    baslik = (baslik or "").strip()
    if not baslik or not url.startswith("http"):
        return None
    metin = fold_tr(f"{baslik} {sirket} {ozet}")
    il = sehir.strip()
    return {
        "id": kaynak_id,
        "hat": "ozel",
        "kaynak": sirket,
        "kaynak_kod": "ats",
        "baslik": baslik,
        "kurum": sirket,
        "il": il,
        "ilce": "",
        "bolge": il_to_bolge(il) if il else "Bilinmiyor",
        "tarih": (tarih or "")[:10],
        "son_basvuru": None,
        "url": url,
        "ozet": ozet[:300],
        "detay": ek_detay or {},
        "ilk_gorulme": bugun,
        "bolumler": _bolum_etiketle(metin),
        "calisma_sekli": _ats_calisma(workplace, metin),
        "istihdam_turu": V2_BILINMIYOR,
        "deneyim": V2_BILINMIYOR,
        "pozisyon_etiket": [],
        "kpss": False,  # özel sektör ATS panoları
        "maas": None,
    }


def _scrape_ats(session: requests.Session) -> list[dict]:
    from unisense.infrastructure.scrapers.kariyer_registry import sirket_ats
    kayitlar: list[dict] = []
    bugun = date.today().isoformat()
    for girdi in sirket_ats():
        if girdi.get("ats") not in ("lever", "ashby"):
            continue  # breezy/successfactors sonraki iş
        sirket = (girdi.get("sirket") or "").strip()
        pano = (girdi.get("pano") or "").strip()
        if not sirket or not pano:
            continue
        try:
            if girdi["ats"] == "lever":
                r = session.get(f"https://api.lever.co/v0/postings/{pano}?mode=json",
                                timeout=REQUEST_TIMEOUT)
                r.raise_for_status()
                ads = r.json() or []
                for ad in ads:
                    if not isinstance(ad, dict):
                        continue
                    cat = ad.get("categories") or {}
                    k = _ats_kayit(
                        kaynak_id=f"ats-lever:{pano}:{ad.get('id')}",
                        kaynak_ad="Lever", sirket=sirket,
                        baslik=ad.get("text") or "",
                        sehir=cat.get("location") or "",
                        tarih=_ms_tarih(ad.get("createdAt")),
                        url=ad.get("hostedUrl") or "",
                        ozet=_temizle_ham(ad.get("descriptionPlain") or ""),
                        workplace=ad.get("workplaceType"),
                        bugun=bugun,
                        ek_detay={"takim": cat.get("team", ""),
                                  "taahhut": cat.get("commitment", "")})
                    if k:
                        kayitlar.append(k)
            else:
                r = session.get(
                    f"https://api.ashbyhq.com/posting-api/job-board/{pano}",
                    timeout=REQUEST_TIMEOUT)
                r.raise_for_status()
                ads = (r.json() or {}).get("jobs") or []
                for ad in ads:
                    if not isinstance(ad, dict):
                        continue
                    loc = ad.get("location")
                    if isinstance(loc, dict):
                        loc = loc.get("name") or ""
                    adr = ad.get("address") or {}
                    post = adr.get("postalAddress") or {} if isinstance(adr, dict) else {}
                    sehir = ((ad.get("locationName") or loc or post.get("addressLocality") or "")
                             .strip())
                    k = _ats_kayit(
                        kaynak_id=f"ats-ashby:{pano}:{ad.get('id')}",
                        kaynak_ad="Ashby", sirket=sirket,
                        baslik=ad.get("title") or "",
                        sehir=sehir,
                        tarih=(ad.get("publishedAt") or "")[:10],
                        url=ad.get("jobUrl") or "",
                        ozet=_temizle_ham(ad.get("descriptionPlain") or ""),
                        workplace=ad.get("workplaceType"),
                        bugun=bugun,
                        ek_detay={"departman": ad.get("department") or "",
                                  "tur": ad.get("employmentType") or ""})
                    if k:
                        kayitlar.append(k)
            print(f"  ats/{pano}: done")
        except Exception as e:  # noqa: BLE001 — pano bazında tolerans
            print(f"  ⚠️ ats/{pano}: {type(e).__name__}")
            continue
    print(f"  ats: {len(kayitlar)} ilan")
    return kayitlar


def _ms_tarih(ms) -> str:
    try:
        return datetime.fromtimestamp(int(ms) / 1000, tz=UTC).date().isoformat()
    except (ValueError, TypeError, OSError):
        return ""


def _merge(yeni: list[dict], eski: list[dict]) -> list[dict]:
    """Birleştirme (union): yeniler + eskiden kalanlar.

    Artımlı taramada (BİK erken-duruş) çekilmeyen eski kayıtlar SİLİNMEZ —
    yoksa her koşu pencereyi daraltır. Temizlik iki koldan: 30 günden
    eskiler budanır; son_basvurusu 7+ gün geçmişler düşer.
    """
    bugun = date.today()
    eski_map = {_v2_id(x): x for x in eski if x.get("id")}
    birlesik: list[dict] = []
    budanan = 0
    gorulen: set[str] = set()
    for k in yeni:
        onceki = eski_map.get(_v2_id(k))
        if onceki and onceki.get("ilk_gorulme"):
            k = {**k, "ilk_gorulme": onceki["ilk_gorulme"]}
        gorulen.add(_v2_id(k))
        birlesik.append(k)
    for x in eski:
        xid = _v2_id(x)
        if xid in gorulen:
            continue
        sb = (x.get("son_basvuru") or "")[:10]
        try:
            suresi_dolmus = bool(sb) and (bugun - date.fromisoformat(sb)).days > 7
        except ValueError:
            suresi_dolmus = False
        if suresi_dolmus:
            budanan += 1
            continue
        birlesik.append(x)
    for k in list(birlesik):
        # son_basvuru VARSA tek ölçüt odur: dolmuşsa at, dolmamışsa KORU.
        # Yaş kuralı uygulanmaz — aksi halde uzun süre açık kalan ilanlar
        # (kurumsal genel başvuru havuzları) yayın tarihi eskidiği için
        # siliniyordu: Savunma Kariyer 24 -> 12, Kariyer Kapısı 33 -> 30
        # (14 AÇIK ilan kaybı, 2026-09-05 ölçümü).
        ksb = (k.get("son_basvuru") or "")[:10]
        if ksb:
            try:
                if (bugun - date.fromisoformat(ksb)).days > 7:
                    birlesik.remove(k)
                    budanan += 1
            except ValueError:
                pass
            continue
        ref = (k.get("tarih") or k.get("ilk_gorulme") or "")[:10]
        try:
            yas = (bugun - date.fromisoformat(ref)).days if ref else 0
        except ValueError:
            yas = 0
        if yas > SAKLA_GUN:
            birlesik.remove(k)
            budanan += 1
    if budanan:
        print(f"  ✂ {budanan} kayıt budandı (30 gün / süresi dolmuş)")
    return birlesik


def main(argv: list[str] | None = None) -> None:
    if sys.platform == "win32":
        # Konsol UTF-8 değilse Türkçe karakterler kırılır. BİLEREK main() içinde:
        # modül import'unda stdout değiştirmek pytest capture'ı bozuyordu.
        import io as _io
        sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    import argparse as _ap
    _par = _ap.ArgumentParser(prog="kariyer_scraper")
    _par.add_argument("--hat", choices=("kamu", "ozel"), action="append",
                      default=None,
                      help="Yalnız bu hatlar koşar (F5.1 bölünmüş cron); "
                           "verilmezse tümü. Diğer hat union ile korunur.")
    _args = _par.parse_args(argv)
    hatlar = set(_args.hat) if _args.hat else None
    if hatlar:
        print(f"  hat filtresi: {sorted(hatlar)}")
    eski: list[dict] = []
    if OUT.exists():
        try:
            data = json.loads(OUT.read_text(encoding="utf-8"))
            eski = data if isinstance(data, list) else []
        except Exception as e:
            print(f"  ⚠️ mevcut dosya okunamadı: {e}")
    try:
        bilinen = {_v2_id(x) for x in eski if x.get("id")}
        detayli = {x.get("id") for x in eski
                   if (x.get("detay") or {}).get("detay_okundu")}
        yeni, hatalar = scrape(bilinen, detayli, hatlar)
    except Exception as e:
        print(f"\n⛔ scrape çöktü ({type(e).__name__}: {e}) — {OUT.name} GÜNCELLENMEDİ")
        sys.exit(1)
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
