"""Resmî Gazete scraper — Hat A (kamu) günlük sayı sinyalleri.

Çıktı: list[dict] — her kayıt bir günlük RG sayısını temsil eder (PDF linkleri + eşleşme sayaçları).
"""
from __future__ import annotations

import time
from datetime import date
from pathlib import Path

import fitz  # PyMuPDF
import requests

from unisense.core.text import fold_tr

RG_HOME = "https://www.resmigazete.gov.tr/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


# RG ve Jooble sunucuları ara sertifikayı göndermiyor; Windows deposu
# önbellekten tamamlıyor ama çıplak OpenSSL/certifi zinciri kuramıyor
# (yerel + CI'da CERTIFICATE_VERIFY_FAILED). Çözüm: herkese açık zincir
# (aralar + kökler, sır değil) repoda paketlenir, oturum bunu kullanır.
_CHAIN = Path(__file__).resolve().parent / "tls_extra_chain.pem"

MAX_PDF_BYTES = 64 * 1024 * 1024
REQUEST_TIMEOUT = 60
KIBAR_BEKELEME = 1.0
MAKS_DENEME = 3
DENEME_KATSAYI = 2.0


def _istek(session: requests.Session, yontem: str, url: str, **kw) -> requests.Response:
    """Merkezi istek politikası: üstel geri çekilmeli yeniden deneme."""
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


def _get(session: requests.Session, url: str, **kw) -> requests.Response:
    return _istek(session, "GET", url, **kw)


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
    """Ana sayfadaki PDF linklerinden tarih → pdf listesi çıkarır."""
    import re
    bulunan: dict[str, list[str]] = {}
    for m in re.finditer(r"https://www\.resmigazete\.gov\.tr/eskiler/(\d{4})/(\d{2})/(\d{8})(-\d+)?\.pdf", html):
        yil, ay, tarih, _sonek = m.group(1), m.group(2), m.group(3), m.group(4)
        gun = f"{tarih[0:4]}-{tarih[4:6]}-{tarih[6:8]}"
        if not (yil == gun[0:4] and ay == gun[5:7]):
            continue
        bulunan.setdefault(gun, [])
        if m.group(0) not in bulunan[gun]:
            bulunan[gun].append(m.group(0))
    return bulunan


def _pdf_metni(session: requests.Session, url: str, limit: int) -> tuple[str, int] | None:
    """PDF'i indirip metnini çıkarır. (metin, sayfa_sayısı) ya da None."""
    r = _get(session, url)
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


def scrape_rg(session: requests.Session | None = None) -> list[dict]:
    """Resmî Gazete günlük sayıları (sinyal kayıtları)."""
    from unisense.core.text import fold_tr

    session = session or _session()
    kayitlar: list[dict] = []
    rg_url = RG_HOME
    pdf_limit = MAX_PDF_BYTES

    r = _get(session, rg_url)
    r.raise_for_status()
    sayilar = _gunluk_sayilar(r.text)
    print(f"  RG ana sayfa: {len(sayilar)} günlük sayı bulundu")

    bugun = date.today().isoformat()
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
            metin_fold = fold_tr(metin)
            for grup, sayi in _eslesme_say(metin_fold).items():
                toplam_eslesme[grup] += sayi

        if sum(toplam_eslesme.values()) == 0:
            continue

        # ID: rg-YYYY-MM-DD
        kid = f"rg-{gun}"
        kayit = {
            "id": kid,
            "hat": "kamu",
            "kaynak": "Resmî Gazete",
            "baslik": f"RG {gun} — bilişim/mühendis/personel sinyalleri",
            "kurum": "Resmî Gazete",
            "sehir": "Ankara",
            "tarih": gun,
            "url": RG_HOME,
            "ozet": f"{sum(toplam_eslesme.values())} sinyal ({toplam_sayfa} sayfa, {len(pdfler)} PDF)",
            "detay": {
                "eslesme": toplam_eslesme,
                "pdfler": pdfler,
                "sayfa": toplam_sayfa,
            },
            "ilk_gorulme": bugun,
            "yeni": True,
        }
        kayitlar.append(kayit)

    print(f"  RG: {len(kayitlar)} sinyal kaydı üretildi")
    return kayitlar


if __name__ == "__main__":
    scrape_rg()