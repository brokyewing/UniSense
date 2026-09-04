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
  {id, hat, kaynak, baslik, kurum, sehir, tarih, url, ozet, detay, ilk_gorulme}

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
from datetime import date, datetime, timezone
from pathlib import Path

import fitz  # PyMuPDF
import requests

from unisense.core.text import fold_tr
from unisense.infrastructure.scrapers._guard import ScrapeGuardError, write_json_guarded

RG_HOME = "https://www.resmigazete.gov.tr/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
OUT = Path(__file__).resolve().parents[4] / "data" / "processed" / "kariyer_ilanlar.json"

# RG ve Jooble sunucuları ara sertifikayı göndermiyor; Windows deposu
# önbellekten tamamlıyor ama çıplak OpenSSL/certifi zinciri kuramıyor
# (yerel + CI'da CERTIFICATE_VERIFY_FAILED). Çözüm: herkese açık zincir
# (aralar + kökler, sır değil) repoda paketlenir, oturum bunu kullanır.
_CHAIN = Path(__file__).resolve().parent / "tls_extra_chain.pem"

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
    hatb = _scrape_hatb(session)
    if hatb:
        print(f"  Hat B: {len(hatb)} ilan (jooble+careerjet)")
    return kayitlar + hatb


# === Hat B: Jooble + Careerjet (API anahtarlı) ===

_HATB_JOOBLE_SORGULAR = [
    ("yazılım geliştirici", "Türkiye"),
    ("bilgisayar mühendisi", "Türkiye"),
]
_HATB_CJ_SORGULAR = ["yazılım", "bilgisayar mühendisi"]
_HATB_SAYFA = 2          # kota dostu: Jooble varsayılan anahtarı 500 istek
_CJ_UC = "http://public.api.careerjet.net/search"  # HTTPS yok (sağlayıcı tarafı)
_CJ_REFERER = os.environ.get("CAREERJET_REFERER", "http://localhost/")


def _temizle_ham(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


def _jooble_normalize(job: dict, bugun: str) -> dict | None:
    baslik = (job.get("title") or "").strip()
    link = (job.get("link") or "").strip()
    if not baslik or not link.startswith("http"):
        return None
    jid = str(job.get("id") or hashlib.sha1(link.encode()).hexdigest()[:12])
    return {
        "id": f"jooble-{jid}",
        "hat": "ozel",
        "kaynak": "Jooble",
        "baslik": baslik,
        "kurum": (job.get("source") or "").strip(),  # Jooble kaynak panoyu verir, işvereni değil
        "sehir": (job.get("location") or "").strip(),
        "tarih": (job.get("updated") or bugun)[:10],
        "url": link,
        "ozet": _temizle_ham(job.get("snippet") or "")[:500],
        "detay": {"maas": (job.get("salary") or "").strip(), "tur": (job.get("type") or "").strip()},
        "ilk_gorulme": bugun,
    }


def _careerjet_normalize(job: dict, bugun: str) -> dict | None:
    baslik = (job.get("title") or "").strip()
    link = (job.get("url") or "").strip()
    if not baslik or not link.startswith("http"):
        return None
    return {
        "id": f"cj-{hashlib.sha1(link.encode()).hexdigest()[:12]}",
        "hat": "ozel",
        "kaynak": "Careerjet",
        "baslik": baslik,
        "kurum": (job.get("company") or "").strip(),
        "sehir": (job.get("locations") or "").strip(),
        "tarih": (job.get("date") or bugun)[:10],
        "url": link,
        "ozet": _temizle_ham(job.get("description") or "")[:500],
        "detay": {"maas": (job.get("salary") or "").strip(), "site": (job.get("site") or "").strip()},
        "ilk_gorulme": bugun,
    }


def _scrape_hatb(session: requests.Session) -> list[dict]:
    """Jooble + Careerjet sorguları. Anahtar yoksa [] döner (atlama, hata değil)."""
    kayitlar: list[dict] = []
    bugun = date.today().isoformat()
    jooble_key = os.environ.get("JOOBLE_API_KEY", "").strip()
    if jooble_key:
        for keywords, location in _HATB_JOOBLE_SORGULAR:
            for page in range(1, _HATB_SAYFA + 1):
                try:
                    r = session.post(f"https://tr.jooble.org/api/{jooble_key}",
                                     json={"keywords": keywords, "location": location, "page": page},
                                     timeout=REQUEST_TIMEOUT)
                    r.raise_for_status()
                    jobs = r.json().get("jobs") or []
                except Exception as e:  # noqa: BLE001
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
    cj_affid = os.environ.get("CAREERJET_API_KEY", "").strip()
    if cj_affid:
        for keywords in _HATB_CJ_SORGULAR:
            for page in range(1, _HATB_SAYFA + 1):
                try:
                    r = session.get(_CJ_UC, params={
                        "locale_code": "tr_TR", "keywords": keywords, "location": "",
                        "affid": cj_affid, "user_ip": "127.0.0.1",
                        "user_agent": HEADERS["User-Agent"],
                        "page": page, "pagesize": 50,
                    }, headers={"Referer": _CJ_REFERER}, timeout=REQUEST_TIMEOUT)
                    r.raise_for_status()
                    data = r.json()
                except Exception as e:  # noqa: BLE001
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
