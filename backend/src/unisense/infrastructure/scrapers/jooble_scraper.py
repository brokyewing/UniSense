"""Jooble API scraper — Hat B (özel sektör).

API: POST https://tr.jooble.org/api/{JOOBLE_API_KEY}
Ülke subdomaini şart (tr.jooble.org), global host WAF 403.
Anahtar: https://jooble.org/api/about — env JOOBLE_API_KEY.
Anahtar yoksa sessizce atlanır (hata değil).
"""
from __future__ import annotations

import hashlib
import os
import time
from datetime import date

import requests

from unisense.core.text import fold_tr
from unisense.infrastructure.scrapers.kariyer_registry import aktifler as _aktif_kaynaklar

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
KIBAR_BEKELEME = 1.0
REQUEST_TIMEOUT = 60
MAKS_DENEME = 3
DENEME_KATSAYI = 2.0


# Geniş çekim: bölüm-agnostik sorgular, etiketleme yerelde yapılır.
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
_HATB_SAYFA_JOOBLE = 5
SAKLA_GUN = 30


def _defter() -> dict[str, dict]:
    return {g["kod"]: g for g in _aktif_kaynaklar()}


def _istek(session: requests.Session, yontem: str, url: str, **kw) -> requests.Response:
    kw.setdefault("timeout", REQUEST_TIMEOUT)
    son_hata: Exception | None = None
    for deneme in range(1, MAKS_DENEME + 1):
        try:
            r = session.request(yontem, url, **kw)
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            r.raise_for_status()
            return r
        except requests.HTTPError as e:
            kod = e.response.status_code if e.response is not None else 0
            if 400 <= kod < 500:
                raise
            son_hata = e
        except (requests.Timeout, requests.ConnectionError) as e:
            son_hata = e
        if deneme < MAKS_DENEME:
            time.sleep(KIBAR_BEKELEME * (DENEME_KATSAYI ** (deneme - 1)))
    raise son_hata  # type: ignore[misc]


def _post(session: requests.Session, url: str, **kw) -> requests.Response:
    return _istek(session, "POST", url, **kw)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    return s


def _tarih_iso(ham: str | None, bugun: str) -> str:
    """RFC-822 / ISO / epoch → YYYY-MM-DD. Parse edilemezse bugün."""
    from email.utils import parsedate_to_datetime
    if not ham:
        return bugun
    try:
        dt = parsedate_to_datetime(ham)
        return dt.date().isoformat()
    except Exception:
        return bugun


def _temizle_ham(s: str) -> str:
    return " ".join(s.replace("\n", " ").replace("\r", " ").split())


# Bölüm anahtarları ÖNceden fold'lu (ascii) yazılır; metin fold_tr ile eşleşir.
# Kaynak: PDF nitelik kodları + yaygın mühendislik bölümleri.
BÖLÜM_ANAHTAR: dict[str, list[str]] = {
    "bilgisayar": ["bilgisayar muhendis", "computer engineer", "bilgisayar programc"],
    "yazilim": ["yazilim muhendis", "yazilim gelistir", "software engineer",
                "software developer", "frontend developer", "backend developer",
                "full stack developer", "devops engineer", "data engineer"],
    "elektrik": ["elektrik muhendis", "electrical engineer", "elektrik tekniker"],
    "elektronik": ["elektronik muhendis", "electronics engineer", "elektronik tekniker"],
    "makine": ["makine muhendis", "mechanical engineer", "makine tekniker"],
    "endustri": ["endustri muhendis", "industrial engineer", "uretim muhendis",
                 "kalite muhendis", "planlama muhendis"],
    "insaat": ["insaat muhendis", "civil engineer", "insaat tekniker", "yol muhendis"],
    "kimya": ["kimya muhendis", "chemical engineer", "proses muhendis", "petrol muhendis"],
    "biyomedikal": ["biyomedikal muhendis", "biomedical engineer", "biyomedikal tekniker"],
    "havacilik": ["havacilik muhendis", "aerospace engineer", "ucak muhendis"],
    "uzay": ["uzay muhendis", "space engineer"],
    "otomotiv": ["otomotiv muhendis", "automotive engineer"],
    "mimarlik": ["mimarlik", "architecture", "mimar"],
    "ic_mimarlik": ["ic mimarlik", "interior architecture", "ic mimar"],
    "sehir_plani": ["sehir plani", "sehir ve bolge pl", "urban planner"],
    "peyzaj": ["peyzaj mimarlik", "landscape architect"],
    "tip": ["tip fakultesi", "medicine", "doktor", "hekim", "tıp"],
    "dis": ["dis hekimligi", "dentistry", "dis hekimi"],
    "eczacilik": ["eczacilik", "pharmacy", "eczaci"],
    "hemsirelik": ["hemsirelik", "nursing", "hemsire"],
    "fizyoterapi": ["fizyoterapi", "physiotherapy"],
    "veteriner": ["veteriner", "veterinary"],
    "muhendis": ["muhendis", "engineer", "engineering"],
    "tekniker": ["tekniker", "technician"],
    "yapay_zeka": ["yapay zeka", "artificial intelligence", "machine learning", "ml engineer"],
    "veri_bilim": ["veri bilim", "data science", "data scientist", "data analyst", "veri analist"],
    "siber_guvenlik": ["siber guvenlik", "cyber security", "information security", "saglik guvenlik"],
    "muhasebe": ["muhasebe", "accounting", "muhasebeci", "mali muhasebe", "cpa"],
    "satis": ["satis", "sales", "satis temsilcisi", "sales representative", "musteri temsilcisi"],
    "pazarlama": ["pazarlama", "marketing", "digital marketing", "sosyal medya", "brand manager"],
    "insan_kaynaklari": ["insan kaynaklari", "human resources", "hr", "ik", "is ve calisma"],
    "hukuk": ["hukuk", "law", "avukat", "hukukcu", "legal counsel"],
    "lojistik": ["lojistik", "logistics", "sevkiyat", "tedarik zinciri", "supply chain"],
    "ticaret": ["dis ticaret", "foreign trade", "ithalat ihracat", "ticaret"],
    "bankacilik": ["bankacilik", "banking", "kredi", "kredi analist", "bank subesi"],
    "sigorta": ["sigorta", "insurance", "actuary", "actuaria"],
    "yazilim_test": ["test muhendis", "qa engineer", "test automation", "sdET"],
    "sistem": ["sistem muhendis", "system engineer", "system admin", "linux admin"],
    "network": ["network muhendis", "network engineer", "ccna", "ccnp"],
    "veritabani": ["veritabani", "database admin", "dba", "sql", "oracle dba"],
    "erp": ["erp", "sap", "oracle erp", "logo", "logo erp"],
    "proje_yonetimi": ["proje yonetimi", "project manager", "pmp", "scrum master", "agile coach"],
    "urun_yonetimi": ["urun yonetimi", "product manager", "product owner"],
    "tasarim": ["ui ux", "ui/ux", "product designer", "grafik tasarim", "grafiker"],
    "ogretmen": ["ogretmen", "teacher", "egitim", "akademik", "ogretim gorevlisi", "ogretim uyesi"],
    "akademik": ["arastirma gorevlisi", "research assistant", "postdoc", "profesor", "docent"],
}


def _bolum_etiketle(metin_fold: str) -> list[str]:
    """Metin içindeki anahtar kelimelere göre bölüm etiketleri döner."""
    etiketler = set()
    for bolum, anahtarlar in BÖLÜM_ANAHTAR.items():
        for kw in anahtarlar:
            if kw in metin_fold:
                etiketler.add(bolum)
                break
    return sorted(etiketler)


def _calisma_sekli(metin_fold: str) -> str:
    """Metinden çalışma şekli çıkarımı (online/hibrit/yuzyuze/bilinmiyor)."""
    if any(k in metin_fold for k in ("uzaktan", "remote", "home office", "evden calis", "e-uzaktan", "tam uzaktan")):
        return "online"
    if any(k in metin_fold for k in ("hibrit", "hybrid", "yarim uzaktan", "esnek calisma")):
        return "hibrit"
    if any(k in metin_fold for k in ("yuz yuze", "yüz yüze", "on site", "ofis", "ofiste", "calisma alani", "is yerinde")):
        return "yuzyuze"
    return "bilinmiyor"


def _istihdam_turu_metinden(ham: str | None) -> str:
    if not ham:
        return "bilinmiyor"
    h = fold_tr(ham)
    if any(k in h for k in ("tam zamanli", "full time", "full-time", "tam zamanlı")):
        return "tam_zamanli"
    if any(k in h for k in ("yarı zamanli", "yari zamanli", "part time", "part-time", "yarı zamanlı")):
        return "yari_zamanli"
    if any(k in h for k in ("staj", "intern", "internship")):
        return "staj"
    if any(k in h for k in ("gecici", "geçici", "temporary", "contract", "sozlesmeli")):
        return "gecici"
    return "bilinmiyor"


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
        "kurum": (job.get("source") or "").strip(),
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


def scrape_jooble(session: requests.Session | None = None) -> list[dict]:
    """Jooble sorgularını çek, normalize et, liste döndür."""
    session = session or _session()
    kayitlar: list[dict] = []
    bugun = date.today().isoformat()
    defter = _defter()
    jooble_key = os.environ.get(
        (defter.get("jooble") or {}).get("env_key", "JOOBLE_API_KEY"), "").strip()
    if not jooble_key:
        print("  ○ JOOBLE_API_KEY yok — Jooble atlandı")
        return []
    sorgular = (defter.get("jooble") or {}).get("sorgular") or _HATB_JOOBLE_SORGULAR
    sayfa_n = int((defter.get("jooble") or {}).get("sayfa", _HATB_SAYFA_JOOBLE))

    for keywords, location in sorgular:
        for page in range(1, sayfa_n + 1):
            try:
                r = _post(session, f"https://tr.jooble.org/api/{jooble_key}",
                          json={"keywords": keywords, "location": location, "page": page})
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

    # Aynı link iki sorguda da çıkabilir → id ile tekille
    tekil = list({k["id"]: k for k in kayitlar}.values())
    return tekil


if __name__ == "__main__":
    scrape_jooble()