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

Kayıt şeması (liste, guard uyumlu):
  {id, hat, kaynak, baslik, kurum, sehir, tarih, url, ozet, detay, ilk_gorulme}

Çıktı: data/processed/kariyer_ilanlar.json (liste)
Kullanım: python -m unisense.infrastructure.scrapers.kariyer_scraper
"""
from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF
import requests

from unisense.core.text import fold_tr
from unisense.infrastructure.scrapers._guard import ScrapeGuardError, write_json_guarded

RG_HOME = "https://www.resmigazete.gov.tr/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
OUT = Path(__file__).resolve().parents[4] / "data" / "processed" / "kariyer_ilanlar.json"

# RG sunucusu ara sertifikayı (GeoTrust TLS RSA CA G1) göndermiyor; Windows
# deposu önbellekten tamamlıyor ama çıplak OpenSSL/certifi zinciri kuramıyor
# (yerel + CI'da CERTIFICATE_VERIFY_FAILED). Çözüm: herkese açık zincir
# (ara + kök, sır değil) repoda paketlenir, oturum bunu kullanır.
_CHAIN = Path(__file__).resolve().parent / "rg_chain.pem"

MAX_PDF_BYTES = 64 * 1024 * 1024   # ana sayı ~30MB olur; daha büyükler atlanır
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


def _pdf_metni(session: requests.Session, url: str) -> tuple[str, int] | None:
    """PDF'i indirip metnini çıkarır. (metin, sayfa_sayısı) ya da None."""
    r = session.get(url, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    if len(r.content) > MAX_PDF_BYTES:
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


def scrape() -> list[dict]:
    kayitlar: list[dict] = []
    session = _session()
    r = session.get(RG_HOME, timeout=REQUEST_TIMEOUT)
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
                sonuc = _pdf_metni(session, url)
            except Exception as e:  # noqa: BLE001
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
            "id": f"rg-{gun}",
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


def _merge(yeni: list[dict], eski: list[dict]) -> list[dict]:
    """id'ye göre birleştir: eski kaydın ilk_gorulme'si korunur, gerisi güncellenir."""
    eski_map = {x.get("id"): x for x in eski if x.get("id")}
    birlesik: list[dict] = []
    for k in yeni:
        onceki = eski_map.get(k["id"])
        if onceki and onceki.get("ilk_gorulme"):
            k = {**k, "ilk_gorulme": onceki["ilk_gorulme"]}
        birlesik.append(k)
    return birlesik


def main() -> None:
    if sys.platform == "win32":
        # Konsol UTF-8 değilse Türkçe karakterler kırılır. BİLEREK main() içinde:
        # modül import'unda stdout değiştirmek pytest capture'ı bozuyordu.
        import io as _io
        sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    try:
        yeni = scrape()
    except Exception as e:  # noqa: BLE001
        print(f"\n⛔ RG erişilemedi ({type(e).__name__}: {e}) — {OUT.name} GÜNCELLENMEDİ")
        sys.exit(1)
    eski: list[dict] = []
    if OUT.exists():
        try:
            data = json.loads(OUT.read_text(encoding="utf-8"))
            eski = data if isinstance(data, list) else []
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ mevcut dosya okunamadı: {e}")
    birlesik = _merge(yeni, eski)
    try:
        write_json_guarded(OUT, birlesik, label="kariyer")
    except ScrapeGuardError as e:
        print(f"\n⛔ {e}")
        sys.exit(1)
    print(f"  guncelleme: {datetime.now(timezone.utc).strftime('%Y-%m-%d')} "
          f"| kayit: {len(birlesik)}")


if __name__ == "__main__":
    main()
