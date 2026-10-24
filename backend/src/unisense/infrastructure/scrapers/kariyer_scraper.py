"""Kariyer ilan toplayıcı — ana orkestratör.

Alt modüller:
  - rg_scraper: Resmî Gazete günlük sayı sinyalleri (Hat A)
  - jooble_scraper: Jooble API (Hat B)
  - careerjet_scraper: Careerjet API (Hat B)
  - kariyer_merge: v2 migrasyon, çapraz tekilleştirme, 30 günlük pencere
Diğer kaynaklar (kamuilan, kariyerkapisi, akademiktr, ilangovtr, savunmakariyer, turksat, ATS)
burada canlı çekilir; statik rehber _KAYNAKLAR (kariyer_service) içinde.

Çıktı: data/processed/kariyer_ilanlar.json
Kullanım: python -m unisense.infrastructure.scrapers.kariyer_scraper
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from datetime import date
from pathlib import Path

import requests

from unisense.core.text import fold_tr
from unisense.infrastructure.scrapers._guard import write_json_guarded
from unisense.infrastructure.scrapers.careerjet_scraper import scrape_careerjet
from unisense.infrastructure.scrapers.jooble_scraper import scrape_jooble
from unisense.infrastructure.scrapers.kariyer_merge import (
    _bolum_etiketle,
    _calisma_sekli,
    _gecmis_guncelle,
    _istihdam_turu_metinden,
    _kosu_raporu,
    _merge,
    _tarih_iso,
)
from unisense.infrastructure.scrapers.kariyer_registry import aktifler as _aktif_kaynaklar

# Yeni modüller
from unisense.infrastructure.scrapers.rg_scraper import scrape_rg

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
OUT = Path(__file__).resolve().parents[4] / "data" / "processed" / "kariyer_ilanlar.json"
KOSU_DOSYA = Path(__file__).resolve().parents[4] / "data" / "processed" / "kariyer_kosu.json"

# TLS zinciri (RG, Jooble, Careerjet için)
_CHAIN = Path(__file__).resolve().parent / "tls_extra_chain.pem"


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update(HEADERS)
    if _CHAIN.exists():
        s.verify = str(_CHAIN)
    return s


def _defter() -> dict[str, dict]:
    return {g["kod"]: g for g in _aktif_kaynaklar()}


# === Diğer kaynaklar (bu dosyada canlı çekilir) ===

# kamuilan.sbb.gov.tr
def _kamuilan_hidden(html: str, name: str) -> str:
    m = re.search(rf'id="{name}"\s+value="([^"]*)"', html)
    return m.group(1) if m else ""


def _kamuilan_detay(session: requests.Session, url: str) -> str:
    try:
        r = session.get(url, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception:
        return ""


def _scrape_kamuilan(session: requests.Session,
                     bilinen_idler: set[str] | None = None) -> list[dict]:
    kayitlar: list[dict] = []
    bilinen = bilinen_idler or set()
    bugun = date.today().isoformat()
    base = (_defter_cache := _defter()).get("kamuilan", {}).get("url") or "https://kamuilan.sbb.gov.tr/"
    r = session.get(base, timeout=30)
    r.raise_for_status()
    viewstate = _kamuilan_hidden(r.text, "__VIEWSTATE")
    viewgen = _kamuilan_hidden(r.text, "__VIEWSTATEGENERATOR")
    eventval = _kamuilan_hidden(r.text, "__EVENTVALIDATION")
    if not (viewstate and viewgen and eventval):
        print("  ⚠️ kamuilan: ViewState bulunamadı")
        return []
    for sayfa in range(1, 11):
        payload = {
            "__VIEWSTATE": viewstate,
            "__VIEWSTATEGENERATOR": viewgen,
            "__EVENTVALIDATION": eventval,
            "ctl00$ContentPlaceHolder1$GridView1$ctl00$ctl03$ctl01": sayfa,
            "__EVENTTARGET": "ctl00$ContentPlaceHolder1$GridView1",
            "__EVENTARGUMENT": f"Page${sayfa}",
        }
        try:
            r = session.post(base, data=payload, timeout=30)
            r.raise_for_status()
        except Exception as e:
            print(f"  ⚠️ kamuilan sayfa {sayfa}: {type(e).__name__}")
            break
        for m in re.finditer(r'href="([^"]*Detay\.aspx\?IlanId=\d+)"', r.text):
            detay_url = m.group(1)
            if not detay_url.startswith("http"):
                detay_url = "https://kamuilan.sbb.gov.tr/" + detay_url.lstrip("/")
            if detay_url in bilinen:
                continue
            html = _kamuilan_detay(session, detay_url)
            if not html:
                continue
            baslik_m = re.search(r'<span id="lblBaslik"[^>]*>([^<]+)</span>', html)
            kurum_m = re.search(r'<span id="lblKurum"[^>]*>([^<]+)</span>', html)
            sehir_m = re.search(r'<span id="lblSehir"[^>]*>([^<]+)</span>', html)
            tarih_m = re.search(r'<span id="lblTarih"[^>]*>([^<]+)</span>', html)
            son_m = re.search(r'<span id="lblSonBasvuru"[^>]*>([^<]+)</span>', html)
            baslik = baslik_m.group(1).strip() if baslik_m else ""
            kurum = kurum_m.group(1).strip() if kurum_m else ""
            sehir = sehir_m.group(1).strip() if sehir_m else ""
            tarih = tarih_m.group(1).strip() if tarih_m else bugun
            son_basvuru = son_m.group(1).strip() if son_m else None
            if not baslik:
                continue
            kid = f"kamuilan:{hashlib.sha1(detay_url.encode()).hexdigest()[:12]}"
            if kid in bilinen:
                continue
            kayitlar.append({
                "id": kid,
                "hat": "kamu",
                "kaynak": "kamuilan.sbb.gov.tr",
                "baslik": baslik,
                "kurum": kurum,
                "sehir": sehir,
                "tarih": tarih,
                "url": detay_url,
                "ozet": f"{kurum} — {sehir}" if kurum or sehir else baslik[:120],
                "detay": {"son_basvuru": son_basvuru} if son_basvuru else {},
                "ilk_gorulme": bugun,
                "yeni": True,
            })
        time.sleep(1.0)
    return kayitlar


# Kariyer Kapısı RSS
def _scrape_kariyerkapisi(session: requests.Session,
                          bilinen_idler: set[str] | None = None) -> list[dict]:
    kayitlar: list[dict] = []
    bilinen = bilinen_idler or set()
    bugun = date.today().isoformat()
    feed_url = (_defter().get("kariyerkapisi", {}).get("url") or
                "https://kariyerkapisi.gov.tr/rss.xml")
    try:
        r = session.get(feed_url, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"  ⚠️ Kariyer Kapısı RSS: {type(e).__name__}")
        return []
    for item in re.finditer(r"<item>(.*?)</item>", r.text, re.DOTALL):
        blk = item.group(1)
        link_m = re.search(r"<link><!\[CDATA\[(.*?)\]\]></link>", blk)
        baslik_m = re.search(r"<title><!\[CDATA\[(.*?)\]\]></title>", blk)
        desc_m = re.search(r"<description><!\[CDATA\[(.*?)\]\]></description>", blk)
        date_m = re.search(r"<pubDate>(.*?)</pubDate>", blk)
        link = link_m.group(1).strip() if link_m else ""
        baslik = baslik_m.group(1).strip() if baslik_m else ""
        ozet = _temizle_ham(desc_m.group(1))[:500] if desc_m else ""
        tarih = _tarih_iso(date_m.group(1) if date_m else None, bugun)
        if not link or not baslik:
            continue
        kid = f"kariyerkapisi:{hashlib.sha1(link.encode()).hexdigest()[:12]}"
        if kid in bilinen:
            continue
        kayitlar.append({
            "id": kid,
            "hat": "kamu",
            "kaynak": "Kariyer Kapısı",
            "baslik": baslik,
            "kurum": "",
            "sehir": "",
            "tarih": tarih,
            "url": link,
            "ozet": ozet,
            "detay": {},
            "ilk_gorulme": bugun,
            "yeni": True,
        })
    return kayitlar


# AkademikTR
def _akademiktr_parse_liste(html: str) -> list[str]:
    return [m.group(1) for m in re.finditer(r'href="(https://akademiktr\.com/ilan/[^"]+)"', html)]


def _akademiktr_parse_detay(html: str) -> dict:
    baslik = re.search(r'<h1[^>]*class="[^"]*title[^"]*"[^>]*>(.*?)</h1>', html, re.DOTALL)
    kurum = re.search(r'<span[^>]*class="[^"]*kurum[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
    sehir = re.search(r'<span[^>]*class="[^"]*sehir[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
    tarih = re.search(r'<span[^>]*class="[^"]*tarih[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
    son = re.search(r'<span[^>]*class="[^"]*son[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
    return {
        "baslik": _temizle_ham(baslik.group(1)) if baslik else "",
        "kurum": _temizle_ham(kurum.group(1)) if kurum else "",
        "sehir": _temizle_ham(sehir.group(1)) if sehir else "",
        "tarih": _temizle_ham(tarih.group(1)) if tarih else "",
        "son_basvuru": _temizle_ham(son.group(1)) if son else "",
    }


def _scrape_akademiktr(session: requests.Session,
                       bilinen_idler: set[str] | None = None) -> list[dict]:
    kayitlar: list[dict] = []
    bilinen = bilinen_idler or set()
    bugun = date.today().isoformat()
    base = (_defter().get("akademiktr", {}).get("url") or
            "https://akademiktr.com/ilanlar")
    for sayfa in range(1, 11):
        try:
            r = session.get(f"{base}?page={sayfa}", timeout=30)
            r.raise_for_status()
        except Exception as e:
            print(f"  ⚠️ AkademikTR sayfa {sayfa}: {type(e).__name__}")
            break
        linkler = _akademiktr_parse_liste(r.text)
        if not linkler:
            break
        for url in linkler:
            if url in bilinen:
                continue
            try:
                r = session.get(url, timeout=30)
                r.raise_for_status()
            except Exception as e:
                print(f"  ⚠️ AkademikTR detay {url}: {type(e).__name__}")
                continue
            d = _akademiktr_parse_detay(r.text)
            if not d["baslik"]:
                continue
            kid = f"akademiktr:{hashlib.sha1(url.encode()).hexdigest()[:12]}"
            if kid in bilinen:
                continue
            kayitlar.append({
                "id": kid,
                "hat": "kamu",
                "kaynak": "AkademikTR",
                "baslik": d["baslik"],
                "kurum": d["kurum"],
                "sehir": d["sehir"],
                "tarih": d["tarih"] or bugun,
                "url": url,
                "ozet": f"{d['kurum']} — {d['sehir']}" if d["kurum"] or d["sehir"] else d["baslik"][:120],
                "detay": {"son_basvuru": d["son_basvuru"]} if d["son_basvuru"] else {},
                "ilk_gorulme": bugun,
                "yeni": True,
            })
            time.sleep(0.5)
    return kayitlar


# ilan.gov.tr
def _ilangovtr_personel_mi(ad: dict) -> bool:
    k = ad.get("kategori", "").lower()
    return any(w in k for w in ("personel", "alım", "ihale", "istihdam", "alimi"))


def _ilangovtr_normalize(ad: dict, bugun: str) -> dict | None:
    baslik = (ad.get("ilanBaslik") or "").strip()
    link = (ad.get("ilanUrl") or "").strip()
    if not baslik or not link.startswith("http"):
        return None
    ozet = _temizle_ham(ad.get("aciklama") or "")[:500]
    metin = fold_tr(f"{baslik} {ozet}")
    return {
        "id": f"ilangovtr:{hashlib.sha1(link.encode()).hexdigest()[:12]}",
        "hat": "kamu",
        "kaynak": "ilan.gov.tr",
        "baslik": baslik,
        "kurum": (ad.get("kurumAdi") or "").strip(),
        "sehir": (ad.get("il") or "").strip(),
        "tarih": _tarih_iso(ad.get("yayimTarihi"), bugun),
        "url": link,
        "ozet": ozet,
        "detay": {"son_basvuru": (ad.get("sonBasvuruTarihi") or "").strip()} if ad.get("sonBasvuruTarihi") else {},
        "ilk_gorulme": bugun,
        "bolumler": _bolum_etiketle(metin),
        "calisma_sekli": _calisma_sekli(metin),
        "istihdam_turu": _istihdam_turu_metinden((ad.get("calismaSekli") or "").strip()),
    }


def _scrape_ilangovtr(session: requests.Session,
                      bilinen_idler: set[str] | None = None) -> list[dict]:
    kayitlar: list[dict] = []
    bilinen = bilinen_idler or set()
    bugun = date.today().isoformat()
    api = (_defter().get("ilangovtr", {}).get("url") or
           "https://api.ilan.gov.tr/api/services/app/Ad/AdsByFilter")
    payload = {"Sorting": "Id desc", "MaxResultCount": 100, "SkipCount": 0}
    for skip in range(0, 500, 100):
        payload["SkipCount"] = skip
        try:
            r = session.post(api, json=payload, timeout=30)
            if r.status_code == 404:
                print("  ⚠️ ilan.gov.tr API 404 (bot skorlaması?)")
                break
            r.raise_for_status()
        except Exception as e:
            print(f"  ⚠️ ilan.gov.tr skip={skip}: {type(e).__name__}")
            break
        data = r.json()
        ads = data.get("result", {}).get("items") or []
        if not ads:
            break
        sayac = 0
        for ad in ads:
            if not _ilangovtr_personel_mi(ad):
                continue
            k = _ilangovtr_normalize(ad, bugun)
            if k and k["id"] not in bilinen:
                kayitlar.append(k)
                sayac += 1
        print(f"  ilan.gov.tr skip={skip}: {sayac} personel alımı")
        if sayac == 0:
            break
        time.sleep(0.5)
    return kayitlar


# Savunma Kariyer
def _scrape_savunmakariyer(session: requests.Session,
                           bilinen_idler: set[str] | None = None) -> list[dict]:
    kayitlar: list[dict] = []
    bilinen = bilinen_idler or set()
    bugun = date.today().isoformat()
    api = (_defter().get("savunmakariyer", {}).get("url") or
           "https://savunmakariyer.com/api/v1/jobs")
    try:
        r = session.get(api, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"  ⚠️ Savunma Kariyer: {type(e).__name__}")
        return []
    jobs = r.json().get("data") or []
    for j in jobs:
        baslik = (j.get("title") or "").strip()
        link = (j.get("applyUrl") or j.get("url") or "").strip()
        if not baslik or not link.startswith("http"):
            continue
        kid = f"savunmakariyer:{hashlib.sha1(link.encode()).hexdigest()[:12]}"
        if kid in bilinen:
            continue
        ozet = _temizle_ham(j.get("description") or "")[:500]
        metin = fold_tr(f"{baslik} {ozet}")
        kayitlar.append({
            "id": kid,
            "hat": "kamu",
            "kaynak": "Savunma Kariyer",
            "baslik": baslik,
            "kurum": (j.get("company") or "").strip(),
            "sehir": (j.get("city") or "").strip(),
            "tarih": _tarih_iso(j.get("publishDate"), bugun),
            "url": link,
            "ozet": ozet,
            "detay": {"son_basvuru": (j.get("applicationDeadline") or "").strip(),
                      "jobType": (j.get("jobType") or "").strip()} if j.get("applicationDeadline") else {},
            "ilk_gorulme": bugun,
            "bolumler": _bolum_etiketle(metin),
            "calisma_sekli": _calisma_sekli(metin),
            "istihdam_turu": j.get("jobType") or "bilinmiyor",
        })
    return kayitlar


# TÜRKSAT Kariyer
def _scrape_turksat(session: requests.Session,
                    bilinen_idler: set[str] | None = None) -> list[dict]:
    kayitlar: list[dict] = []
    bilinen = bilinen_idler or set()
    bugun = date.today().isoformat()
    api = (_defter().get("turksat", {}).get("url") or
           "https://kariyer.turksat.com.tr/api/v1/jobs")
    try:
        r = session.get(api, timeout=30)
        r.raise_for_status()
    except Exception as e:
        print(f"  ⚠️ TÜRKSAT: {type(e).__name__}")
        return []
    jobs = r.json().get("data") or []
    for j in jobs:
        baslik = (j.get("title") or "").strip()
        link = (j.get("applyUrl") or j.get("url") or "").strip()
        if not baslik or not link.startswith("http"):
            continue
        kid = f"turksat:{hashlib.sha1(link.encode()).hexdigest()[:12]}"
        if kid in bilinen:
            continue
        ozet = _temizle_ham(j.get("description") or "")[:500]
        metin = fold_tr(f"{baslik} {ozet}")
        kayitlar.append({
            "id": kid,
            "hat": "kamu",
            "kaynak": "TÜRKSAT Kariyer",
            "baslik": baslik,
            "kurum": (j.get("company") or "").strip(),
            "sehir": (j.get("city") or "").strip(),
            "tarih": _tarih_iso(j.get("publishDate"), bugun),
            "url": link,
            "ozet": ozet,
            "detay": {"son_basvuru": (j.get("applicationDeadline") or "").strip(),
                      "jobType": (j.get("jobType") or "").strip()} if j.get("applicationDeadline") else {},
            "ilk_gorulme": bugun,
            "bolumler": _bolum_etiketle(metin),
            "calisma_sekli": _calisma_sekli(metin),
            "istihdam_turu": j.get("jobType") or "bilinmiyor",
        })
    return kayitlar


# ATS adaptörleri (Lever, Greenhouse, vb.)
def _ats_calisma(workplace: str | None, metin_fold: str) -> str:
    if workplace:
        w = workplace.lower()
        if "remote" in w:
            return "online"
        if "hybrid" in w:
            return "hibrit"
        return "yuzyuze"
    return _calisma_sekli(metin_fold)


def _ats_kayit(*, kaynak_id: str, kaynak_ad: str, sirket: str, baslik: str,
               url: str, sehir: str, workplace: str | None, metin_fold: str,
               ozet: str, detay_ek: dict | None = None) -> dict:
    bugun = date.today().isoformat()
    kid = f"{kaynak_id}:{hashlib.sha1(f'{kaynak_id}{url}{baslik}'.encode()).hexdigest()[:12]}"
    return {
        "id": kid,
        "hat": "ozel",
        "kaynak": kaynak_ad,
        "baslik": baslik,
        "kurum": sirket,
        "sehir": sehir,
        "tarih": bugun,
        "url": url,
        "ozet": ozet,
        "detay": detay_ek or {},
        "ilk_gorulme": bugun,
        "bolumler": _bolum_etiketle(metin_fold),
        "calisma_sekli": _ats_calisma(workplace, metin_fold),
        "istihdam_turu": "bilinmiyor",
    }


def _scrape_ats(session: requests.Session,
                bilinen_idler: set[str] | None = None) -> list[dict]:
    kayitlar: list[dict] = []
    bilinen = bilinen_idler or set()
    defter = _defter()
    # Lever
    for slug, sirket in (defter.get("lever") or {}).items():
        try:
            r = session.get(f"https://api.lever.co/v0/postings/{slug}?mode=json", timeout=20)
            if r.status_code == 404:
                continue
            r.raise_for_status()
        except Exception:
            continue
        for p in r.json():
            if p.get("categories", {}).get("location"):
                loc = p["categories"]["location"]
                sehir = loc.split(",")[-1].strip()
            else:
                sehir = ""
            workplace = p.get("workplaceType")
            ozet = _temizle_ham(p.get("descriptionPlain") or p.get("description") or "")[:500]
            metin = fold_tr(f"{p.get('text', '')} {ozet}")
            k = _ats_kayit(kaynak_id=f"lever:{slug}", kaynak_ad=f"Lever ({sirket})",
                           sirket=sirket, baslik=p.get("text", ""),
                           url=p.get("applyUrl", ""), sehir=sehir,
                           workplace=workplace, metin_fold=metin, ozet=ozet,
                           detay_ek={"workplaceType": workplace} if workplace else None)
            if k["id"] not in bilinen:
                kayitlar.append(k)
        time.sleep(0.3)
    return kayitlar


# === Yardımcı fonksiyonlar (kariyer_scraper'dan taşındı) ===

def _temizle_ham(s: str) -> str:
    return " ".join(s.replace("\n", " ").replace("\r", " ").split())


# === Ana fonksiyon ===
def main(argv: list[str] | None = None) -> None:
    print("=== Kariyer İlan Toplayıcı ===")
    start = time.perf_counter()

    session = _session()

    # 1. Geçmiş kayıtları oku (kaynak_kod/il/ilce/bolge v2)
    eski: list[dict] = []
    eski_idler: set[str] = set()
    if OUT.exists():
        try:
            eski = json.loads(OUT.read_text(encoding="utf-8"))
            eski_idler = {k.get("id") for k in eski if k.get("id")}
        except Exception as e:
            print(f"  ⚠️ Eski kayıt okunamadı: {e}")

    # 2. Tüm kaynakları çek
    yeni: list[dict] = []

    print("\n[Hat A - Kamu]")
    print("  Resmî Gazete...")
    yeni.extend(scrape_rg(session))

    print("  kamuilan.sbb.gov.tr...")
    yeni.extend(_scrape_kamuilan(session, eski_idler))

    print("  Kariyer Kapısı RSS...")
    yeni.extend(_scrape_kariyerkapisi(session, eski_idler))

    print("  AkademikTR...")
    yeni.extend(_scrape_akademiktr(session, eski_idler))

    print("  ilan.gov.tr...")
    yeni.extend(_scrape_ilangovtr(session, eski_idler))

    print("  Savunma Kariyer...")
    yeni.extend(_scrape_savunmakariyer(session, eski_idler))

    print("  TÜRKSAT Kariyer...")
    yeni.extend(_scrape_turksat(session, eski_idler))

    print("  ATS (Lever)...")
    yeni.extend(_scrape_ats(session, eski_idler))

    print("\n[Hat B - Özel]")
    print("  Jooble...")
    yeni.extend(scrape_jooble(session))

    print("  Careerjet...")
    yeni.extend(scrape_careerjet(session))

    print(f"\nToplam yeni çekilen: {len(yeni)}")

    # 3. Merge (v2 migrasyon + çapraz tekilleştirme + 30 günlük pencere)
    birlesik = _merge(yeni, eski)

    # 4. Yaz (guard'lı)
    write_json_guarded(OUT, birlesik)

    # 5. Kosu raporu + geçmiş güncelle
    bugun = date.today().isoformat()
    cekilen = _kosu_raporu(yeni, eski_idler, bugun)
    _gecmis_guncelle(KOSU_DOSYA, bugun, cekilen)

    elapsed = time.perf_counter() - start
    print(f"\nBitti: {len(birlesik)} kayıt → {OUT} ({elapsed:.1f}s)")


if __name__ == "__main__":
    main()