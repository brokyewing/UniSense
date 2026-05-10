"""Türkiye coğrafi haritalar — il, bölge, KKTC.

Sahil/metropol/merkez ilçe metadatası `data/raw/turkey_geo.json` dosyasından gelir.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path


REGIONS: dict[str, list[str]] = {
    "Marmara": [
        "İSTANBUL", "BURSA", "KOCAELİ", "TEKİRDAĞ", "BALIKESİR", "ÇANAKKALE",
        "EDİRNE", "KIRKLARELİ", "SAKARYA", "YALOVA", "BİLECİK",
    ],
    "Ege": [
        "İZMİR", "MANİSA", "AYDIN", "DENİZLİ", "MUĞLA", "AFYONKARAHİSAR",
        "KÜTAHYA", "UŞAK",
    ],
    "Akdeniz": [
        "ANTALYA", "ADANA", "MERSİN", "HATAY", "BURDUR", "ISPARTA",
        "OSMANİYE", "KAHRAMANMARAŞ",
    ],
    "İç Anadolu": [
        "ANKARA", "KONYA", "KAYSERİ", "ESKİŞEHİR", "AKSARAY", "ÇANKIRI",
        "KIRIKKALE", "KIRŞEHİR", "NEVŞEHİR", "NİĞDE", "SİVAS", "YOZGAT",
        "KARAMAN",
    ],
    "Karadeniz": [
        "SAMSUN", "TRABZON", "ORDU", "GİRESUN", "RİZE", "ARTVİN",
        "BARTIN", "BAYBURT", "BOLU", "ÇORUM", "DÜZCE", "GÜMÜŞHANE",
        "KASTAMONU", "KARABÜK", "SİNOP", "TOKAT", "ZONGULDAK", "AMASYA",
    ],
    "Doğu Anadolu": [
        "ERZURUM", "MALATYA", "ELAZIĞ", "VAN", "AĞRI", "ARDAHAN",
        "BİNGÖL", "BİTLİS", "ERZİNCAN", "HAKKARİ", "IĞDIR", "KARS",
        "MUŞ", "TUNCELİ",
    ],
    "Güneydoğu Anadolu": [
        "GAZİANTEP", "DİYARBAKIR", "ŞANLIURFA", "MARDİN", "BATMAN",
        "ADIYAMAN", "KİLİS", "SİİRT", "ŞIRNAK",
    ],
    "KKTC": [
        "GAZİMAĞUSA", "GİRNE", "LEFKE", "LEFKOŞA", "GÜZELYURT", "İSKELE",
    ],
    "Yurtdışı": [
        # Yurtdışı kamu üniversiteleri
    ],
}


def il_to_bolge(il_adi: str | None) -> str:
    """İl adından bölgeyi bul. Bilinmiyorsa 'Bilinmiyor' döner."""
    if not il_adi:
        return "Bilinmiyor"
    il_norm = il_adi.strip().upper()
    for region, cities in REGIONS.items():
        if il_norm in cities:
            return region
    return "Bilinmiyor"


# İl kodu → ad (ÖSYM standart kodları)
PLAKA_KODLARI: dict[int, str] = {
    1: "ADANA", 2: "ADIYAMAN", 3: "AFYONKARAHİSAR", 4: "AĞRI", 5: "AMASYA",
    6: "ANKARA", 7: "ANTALYA", 8: "ARTVİN", 9: "AYDIN", 10: "BALIKESİR",
    11: "BİLECİK", 12: "BİNGÖL", 13: "BİTLİS", 14: "BOLU", 15: "BURDUR",
    16: "BURSA", 17: "ÇANAKKALE", 18: "ÇANKIRI", 19: "ÇORUM", 20: "DENİZLİ",
    21: "DİYARBAKIR", 22: "EDİRNE", 23: "ELAZIĞ", 24: "ERZİNCAN", 25: "ERZURUM",
    26: "ESKİŞEHİR", 27: "GAZİANTEP", 28: "GİRESUN", 29: "GÜMÜŞHANE", 30: "HAKKARİ",
    31: "HATAY", 32: "ISPARTA", 33: "MERSİN", 34: "İSTANBUL", 35: "İZMİR",
    36: "KARS", 37: "KASTAMONU", 38: "KAYSERİ", 39: "KIRKLARELİ", 40: "KIRŞEHİR",
    41: "KOCAELİ", 42: "KONYA", 43: "KÜTAHYA", 44: "MALATYA", 45: "MANİSA",
    46: "KAHRAMANMARAŞ", 47: "MARDİN", 48: "MUĞLA", 49: "MUŞ", 50: "NEVŞEHİR",
    51: "NİĞDE", 52: "ORDU", 53: "RİZE", 54: "SAKARYA", 55: "SAMSUN",
    56: "SİİRT", 57: "SİNOP", 58: "SİVAS", 59: "TEKİRDAĞ", 60: "TOKAT",
    61: "TRABZON", 62: "TUNCELİ", 63: "ŞANLIURFA", 64: "UŞAK", 65: "VAN",
    66: "YOZGAT", 67: "ZONGULDAK", 68: "AKSARAY", 69: "BAYBURT", 70: "KARAMAN",
    71: "KIRIKKALE", 72: "BATMAN", 73: "ŞIRNAK", 74: "BARTIN", 75: "ARDAHAN",
    76: "IĞDIR", 77: "YALOVA", 78: "KARABÜK", 79: "KİLİS", 80: "OSMANİYE",
    81: "DÜZCE",
}


# === Sahil / Merkez / Metropol metadata (turkey_geo.json) ===

def _tr_upper(s: str) -> str:
    """Türkçe-güvenli upper (i→İ, ı→I)."""
    return s.replace("i", "İ").replace("ı", "I").upper()


@lru_cache(maxsize=1)
def _load_geo_json() -> dict:
    here = Path(__file__).resolve()
    project_root = here.parents[3]
    geo_path = project_root / "data" / "raw" / "turkey_geo.json"
    with open(geo_path, encoding="utf-8") as f:
        return json.load(f)


def is_coastal_city(city: str | None) -> bool:
    """İl deniz kıyısı mı?"""
    if not city:
        return False
    return _tr_upper(city) in _load_geo_json()["coastal_cities"]


def get_seas(city: str | None) -> list[str]:
    """İlin kıyısı olduğu denizler."""
    if not city:
        return []
    info = _load_geo_json()["coastal_cities"].get(_tr_upper(city))
    return list(info["seas"]) if info else []


def get_coast_km(city: str | None) -> int | None:
    """İlin kıyı uzunluğu (km)."""
    if not city:
        return None
    info = _load_geo_json()["coastal_cities"].get(_tr_upper(city))
    return info.get("coast_km") if info else None


def is_metropolis(city: str | None) -> bool:
    """Büyükşehir mi?"""
    if not city:
        return False
    return _tr_upper(city) in _load_geo_json()["metropolises"]


def is_central_district(city: str | None, district: str | None) -> bool:
    """İlçe şehrin merkez ilçesi mi?

    "MERKEZ" otomatik True. Büyükşehirlerde merkez ilçe listesi `central_districts` içinde.
    """
    if not district:
        return False
    d_upper = _tr_upper(district)
    if d_upper == "MERKEZ":
        return True
    central = _load_geo_json()["central_districts"].get(_tr_upper(city or ""), [])
    return d_upper in central


def geo_summary(city: str | None, district: str | None) -> dict:
    """Tek üniversite/bölüm için coğrafi özet."""
    return {
        "is_coastal": is_coastal_city(city),
        "seas": get_seas(city),
        "coast_km": get_coast_km(city),
        "is_metropolis": is_metropolis(city),
        "is_central_district": is_central_district(city, district),
    }


def cities_by_sea(sea: str) -> list[str]:
    """Belirli bir denize kıyısı olan iller."""
    sea = sea.strip().capitalize()
    return [
        city
        for city, info in _load_geo_json()["coastal_cities"].items()
        if sea in info["seas"]
    ]


def all_coastal_cities() -> list[str]:
    return list(_load_geo_json()["coastal_cities"].keys())


def all_metropolises() -> list[str]:
    return list(_load_geo_json()["metropolises"])
