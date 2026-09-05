"""Kariyer servisi — günlük ilan sinyalleri + statik kaynak rehberi.

Veri: data/processed/kariyer_ilanlar.json (liste; kariyer_scraper üretir).
Dosya yoksa servis boş liste döner (UI rehber sekmesini her durumda gösterir).

Rehber (_KAYNAKLAR): 21 sayfalık kamu rehberi (Hat A, A1–A18) + career-ops
TR site-sorguları (Hat B). Kodla birlikte sürümlenir — backend/data'ya elle
JSON commit'lenmez (Dokunma kuralı), scraper çıktısı pipeline'dan gelir.
"""
from __future__ import annotations

import json
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from unisense.core.config import get_settings
from unisense.core.text import fold_tr
from unisense.domain.geo import il_to_bolge

YENI_GUN_SAYISI = 7
MAX_LIMIT = 100

# Bölüm taksonomisi (id → görünen ad). Eşleşme scraper'da BÖLÜM_ANAHTAR ile
# yapılır; burası yalnız etiket listesidir — ikisi birlikte güncellenir.
BOLUM_ETIKETLER: dict[str, str] = {
    "bilgisayar": "Bilgisayar Müh.",
    "yazilim": "Yazılım Müh.",
    "elektrik_elektronik": "Elektrik-Elektronik",
    "endustri": "Endüstri Müh.",
    "makine": "Makine Müh.",
    "mekatronik": "Mekatronik/Robotik",
    "insaat": "İnşaat Müh.",
    "yapay_zeka_veri": "YZ / Veri",
    "siber": "Siber Güvenlik",
    "ag_sistem": "Ağ / Sistem / DevOps",
    "tekniker": "Tekniker/Teknisyen",
    "isletme": "İşletme/Finans",
}

# === Statik kaynak rehberi (Hat A: PDF rehberinden; Hat B: career-ops) ===
# tip: portal (doğrudan ilan bakılır) | kurum (kendi duyuru sayfası) |
#      toplayici (resmî değil, hızlı derleme) | site_sorgu (career-ops deseni)
_KAYNAKLAR: list[dict] = [
    # --- Hat A: resmi kamu ---
    {"id": "kariyer-kapisi", "hat": "kamu", "tip": "portal",
     "ad": "Kariyer Kapısı", "url": "https://kariyerkapisi.gov.tr/isealim",
     "not_": "En önemli kanal; sözleşmeli bilişim neredeyse tamamı buradan. e-Devlet girişi gerekir."},
    {"id": "osym", "hat": "kamu", "tip": "portal",
     "ad": "ÖSYM", "url": "https://www.osym.gov.tr",
     "not_": "Merkezi yerleştirme; Kariyer Kapısı'nda görünmez. Sıradaki: KPSS-2026/2 tercihleri 17–24 Aralık 2026."},
    {"id": "yetenek-kapisi", "hat": "kamu", "tip": "portal",
     "ad": "Yetenek Kapısı", "url": "https://www.yetenekkapisi.org",
     "not_": "İş/staj eşleşme; yazılım-mühendislik ilanları yoğun."},
    {"id": "kamuilan-sbb", "hat": "kamu", "tip": "portal",
     "ad": "kamuilan.sbb.gov.tr", "url": "https://kamuilan.sbb.gov.tr",
     "not_": "Resmî arşiv (kurum+yıl); başvuru buradan alınmaz."},
    {"id": "ilan-gov-tr", "hat": "kamu", "tip": "portal",
     "ad": "ilan.gov.tr Personel Alımı", "url": "https://www.ilan.gov.tr/ilan/tum-ilanlar/personel-alimi",
     "not_": "BİK resmî toplayıcı; üyelik + kayıtlı arama + bildirim. Botlara API kapalı."},
    {"id": "iskur", "hat": "kamu", "tip": "portal",
     "ad": "İŞKUR e-Şube", "url": "https://esube.iskur.gov.tr",
     "not_": "Kamu İŞÇİ kadrosu (memur değil); başvuru penceresi ~5 gün. Bot WAF'lı."},
    {"id": "resmi-gazete", "hat": "kamu", "tip": "portal",
     "ad": "Resmî Gazete", "url": "https://www.resmigazete.gov.tr",
     "not_": "A grubu + yedek kanal; günlük tarama bu uygulamadan izlenir."},
    {"id": "ilan-yok", "hat": "kamu", "tip": "portal",
     "ad": "ilan.yok.gov.tr", "url": "https://ilan.yok.gov.tr",
     "not_": "Akademik kadro (ALES+YDS, KPSS değil)."},
    {"id": "vizyoner-genc", "hat": "kamu", "tip": "portal",
     "ad": "Vizyoner Genç", "url": "https://vizyonergenc.com",
     "not_": "Savunma sanayii ortak portalı (YÜKSEK ÖNCELİK, KPSS'siz). Haftalık bülteni aç."},
    {"id": "tubitak", "hat": "kamu", "tip": "kurum",
     "ad": "TÜBİTAK + BİLGEM + ULAKBİM",
     "url": "https://kariyer.tubitak.gov.tr",
     "not_": "kariyer.bilgem.tubitak.gov.tr ve ulakbim.tubitak.gov.tr ayrı takip; çoğu ilanda KPSS yok."},
    {"id": "duzenleyiciler", "hat": "kamu", "tip": "kurum",
     "ad": "TCMB / BDDK / SPK / Sayıştay", "url": "https://insankaynaklari.tcmb.gov.tr",
     "not_": "Kendi portalları; Kariyer Kapısı'nda görünmeyebilir."},
    {"id": "ddo-usom-gib", "hat": "kamu", "tip": "kurum",
     "ad": "DDO / USOM / GİB", "url": "https://cbddo.gov.tr",
     "not_": "Dijital Dönüşüm Ofisi, siber güvenlik (USOM), veri analitiği (GİB)."},
    {"id": "savunma-sirket", "hat": "kamu", "tip": "kurum",
     "ad": "HAVELSAN / ASELSAN / TÜRKSAT / STM", "url": "https://kariyer.havelsan.com.tr",
     "not_": "KPSS'siz doğrudan alım; aselsan.com/tr/kariyer, kariyer.turksat.com.tr, stm.com.tr/tr/kariyer, bites.com.tr, ulak.com.tr."},
    {"id": "banka-teknoloji", "hat": "kamu", "tip": "kurum",
     "ad": "Ziraat Teknoloji / Vakıf Katılım", "url": "https://ziraatteknoloji.com",
     "not_": "Yıl boyu alım, KPSS yok."},
    {"id": "guvenlik-savunma", "hat": "kamu", "tip": "kurum",
     "ad": "Jandarma / MSB / EGM / MİT", "url": "https://personeltemin.msb.gov.tr",
     "not_": "personeltemin.jandarma.gov.tr, pa.edu.tr, mit.gov.tr kariyer sayfası."},
    {"id": "adalet-tbmm", "hat": "kamu", "tip": "kurum",
     "ad": "Adalet Bakanlığı / TBMM", "url": "https://pgm.adalet.gov.tr",
     "not_": "bilgiislem.adalet.gov.tr ve tbmm.gov.tr duyuruları ek izlenir."},
    {"id": "kamu-toplayici", "hat": "kamu", "tip": "toplayici",
     "ad": "memurlar.net / kamuis / isinolsa / kamuajans",
     "url": "https://ilan.memurlar.net",
     "not_": "Resmî değil ama hızlı; başvuru öncesi orijinal ilana bak."},
    {"id": "iskur-acik-is", "hat": "kamu", "tip": "portal",
     "ad": "İŞKUR Açık İş İlanları", "url": "https://www.iskur.gov.tr",
     "not_": "Genel açık iş portalı (özel sektör dahil); kamu işçi alımı e-Şube'den ayrı."},
    {"id": "kamu-sosyal", "hat": "kamu", "tip": "toplayici",
     "ad": "LinkedIn + Telegram/X bilişim hesapları", "url": "https://www.linkedin.com",
     "not_": "Bilişim ilanlarını en hızlı duyuran kanallar; hedef kurumları takip et."},
    {"id": "milli-saraylar", "hat": "kamu", "tip": "kurum",
     "ad": "Milli Saraylar İdaresi", "url": "https://millisaraylar.gov.tr",
     "not_": "Bağımsız idare; düzenli sözleşmeli bilişim + bilgisayar mühendisi alımı."},
    {"id": "spor-toto", "hat": "kamu", "tip": "kurum",
     "ad": "Spor Toto Teşkilatı", "url": "https://www.sportoto.gov.tr",
     "not_": "Merkezi bahis altyapısı için yüksek ücretli sözleşmeli yazılımcı/sistem mühendisi."},
    {"id": "ssb", "hat": "kamu", "tip": "kurum",
     "ad": "Savunma Sanayii Başkanlığı", "url": "https://ssb.gov.tr",
     "not_": "Kendi ilanları; Vizyoner Genç ile birlikte takip et."},
    {"id": "epdk-rekabet-btk", "hat": "kamu", "tip": "kurum",
     "ad": "EPDK / Rekabet Kurumu / BTK", "url": "https://www.epdk.gov.tr",
     "not_": "Uzman yardımcılığı + BT kadroları; rekabet.gov.tr, btk.gov.tr (USOM). 35 yaş sınırına dikkat."},
    {"id": "iletisim", "hat": "kamu", "tip": "kurum",
     "ad": "İletişim Başkanlığı", "url": "https://www.iletisim.gov.tr",
     "not_": "Kendi portalı üzerinden sınav başvurusu açabiliyor; duyurulardan teyit et."},
    {"id": "kamu-bankalari", "hat": "kamu", "tip": "kurum",
     "ad": "Halkbank / Ziraat / VakıfBank", "url": "https://www.halkbank.com.tr",
     "not_": "KPSS'siz kendi yazılı sınavları (ziraatbank.com.tr, vakifbank.com.tr). Yılda bir, ilkbaharda toplu alım."},
    {"id": "csb-yerel", "hat": "kamu", "tip": "kurum",
     "ad": "Çevre Şehircilik (Yerel Yönetimler)", "url": "https://www.csb.gov.tr",
     "not_": "Belediye ilanları 30-gün kuralıyla burada görünür; en güvenilir toplu kaynak."},
    {"id": "sozlesmeli-bilisim", "hat": "kamu", "tip": "kurum",
     "ad": "Sözleşmeli bilişim veren kurumlar", "url": "https://kariyerkapisi.gov.tr/isealim",
     "not_": "MEB, Sanayi-Teknoloji, Aile, Çalışma, TİKA, Adalet + Hazine, GİB, SGK, Sağlık, İçişleri, Ticaret, Ulaştırma, TÜİK, AFAD, DSİ, KGM. P3'ün %30'u; Kalkınma Ajansları (26 ajans) başvurusu da Kariyer Kapısı üzerinden."},
    {"id": "kamuis", "hat": "kamu", "tip": "toplayici",
     "ad": "kamuis.com.tr", "url": "https://kamuis.com.tr",
     "not_": "Resmî değil; hızlı derleme. Başvuru öncesi orijinal ilana bak."},
    {"id": "isinolsa", "hat": "kamu", "tip": "toplayici",
     "ad": "isinolsa.com", "url": "https://www.isinolsa.com",
     "not_": "Resmî değil; hızlı derleme. Başvuru öncesi orijinal ilana bak."},
    {"id": "kamuilan-net", "hat": "kamu", "tip": "toplayici",
     "ad": "kamuilan.net", "url": "https://kamuilan.net",
     "not_": "Resmî değil; hızlı derleme. Başvuru öncesi orijinal ilana bak."},
    {"id": "kamuajans", "hat": "kamu", "tip": "toplayici",
     "ad": "KamuAjans / KamuPersoneli", "url": "https://kamuajans.com",
     "not_": "Belediye ve kalkınma ajansı alımlarını hızlı listeler (kamupersoneli.net)."},
    # --- Hat B: özel sektör (career-ops site-sorgu deseni) ---
    {"id": "kariyer-net", "hat": "ozel", "tip": "site_sorgu",
     "ad": "kariyer.net", "url": "https://www.kariyer.net",
     "not_": "Genel iş portalı; herkese açık ATS API'si yok."},
    {"id": "techcareer", "hat": "ozel", "tip": "site_sorgu",
     "ad": "techcareer.net", "url": "https://techcareer.net",
     "not_": "Teknoloji odaklı; Backend + AI/Python ilanları."},
    {"id": "kodilan", "hat": "ozel", "tip": "site_sorgu",
     "ad": "kodilan.com", "url": "https://kodilan.com",
     "not_": "Yazılım ilanları."},
    {"id": "yeni-mezun", "hat": "ozel", "tip": "site_sorgu",
     "ad": "youthall / toptalent", "url": "https://youthall.com",
     "not_": "Yeni mezun/junior odağı."},
    {"id": "secretcv-yenibiris", "hat": "ozel", "tip": "site_sorgu",
     "ad": "secretcv / yenibiris / isinolsun / eleman.net",
     "url": "https://www.secretcv.com",
     "not_": "Genel portallar; site-sorguyla taranır."},
    {"id": "indeed-careerjet", "hat": "ozel", "tip": "site_sorgu",
     "ad": "tr.indeed / careerjet.com.tr", "url": "https://tr.indeed.com",
     "not_": "Toplayıcılar; careerjet tr_TR destekler."},
    {"id": "elemanonline", "hat": "ozel", "tip": "site_sorgu",
     "ad": "elemanonline", "url": "https://www.elemanonline.com.tr",
     "not_": "Genel iş portalı."},
    {"id": "cvyolla", "hat": "ozel", "tip": "site_sorgu",
     "ad": "cvyolla", "url": "https://www.cvyolla.com",
     "not_": "Genel iş portalı."},
    {"id": "stajim", "hat": "ozel", "tip": "site_sorgu",
     "ad": "stajim.net", "url": "https://stajim.net",
     "not_": "Staj ilanları odağı; yeni mezunlar için."},
    {"id": "jooble", "hat": "ozel", "tip": "site_sorgu",
     "ad": "Jooble TR", "url": "https://tr.jooble.org",
     "not_": "Toplayıcı; bot korumalı (tarayıcıdan açılır)."},
    {"id": "sirket-kariyer", "hat": "ozel", "tip": "kurum",
     "ad": "Trendyol / Turkcell / ASELSAN / Softtech / bankalar",
     "url": "https://kariyer.turkcell.com.tr",
     "not_": "~50 TR şirketi (tam liste PLAN_KARIYER.md Hat B); kendi kariyer sayfaları."},
]


@lru_cache(maxsize=1)
def _load() -> list[dict]:
    p = Path(get_settings().project_root) / "data" / "processed" / "kariyer_ilanlar.json"
    if not p.exists():
        return []
    try:
        data = json.load(open(p, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    return data if isinstance(data, list) else []


def _yeni_mi(ilk_gorulme: str, bugun: date, gun: int = YENI_GUN_SAYISI) -> bool:
    try:
        d = date.fromisoformat((ilk_gorulme or "")[:10])
    except ValueError:
        return False
    return (bugun - d) <= timedelta(days=gun)


def _coklu(v: str | list[str] | None) -> set[str] | None:
    """Tekil ya da çoklu seçim parametresini kümeye çevirir."""
    if v is None:
        return None
    return {v} if isinstance(v, str) else set(v)


def filtrele(kayitlar: list[dict], *, hat: str | None = None,
             q: str | None = None, kaynak: str | None = None,
             sehir: str | None = None, bolum: str | None = None,
             il: str | None = None, bolge: str | None = None,
             ilce: str | None = None, calisma_sekli: str | list[str] | None = None,
             istihdam_turu: str | list[str] | None = None,
             deneyim: str | list[str] | None = None,
             kpss: bool | None = None, sadece_yeni: bool = False,
             yeni_gun: int = YENI_GUN_SAYISI,
             limit: int = 20, sayfa: int = 1, boyut: int = 20,
             sira: str = "tarih_desc", bugun: date | None = None) -> tuple[list[dict], int]:
    """Saf filtre — test edilebilir; cache'li veriyi mutasyona uğratmaz.

    Döner: (sayfadaki kayıtlar, sayfalama ÖNCESİ toplam).
    il: il+sehir alanında alt-dize arar (ham API verisi "İstanbul, Türkiye"
    gibi olabilir); bolge: v2 `bolge` alanında birebir eşleşir.
    """
    bugun = bugun or date.today()
    qf = fold_tr(q) if q else ""
    ilf = fold_tr(il) if il else ""
    ilcef = fold_tr(ilce) if ilce else ""
    cs_set = _coklu(calisma_sekli)
    it_set = _coklu(istihdam_turu)
    dn_set = _coklu(deneyim)
    out: list[dict] = []
    for k in kayitlar:
        if hat and k.get("hat") != hat:
            continue
        if kaynak and k.get("kaynak") != kaynak:
            continue
        if bolum and bolum not in (k.get("bolumler") or []):
            continue
        if sehir and fold_tr(sehir) not in fold_tr(k.get("sehir") or ""):
            continue
        if ilf and ilf not in fold_tr(f"{k.get('il', '')} {k.get('sehir', '')}"):
            continue
        if bolge and fold_tr(bolge) != fold_tr(k.get("bolge") or ""):
            continue
        if ilcef and ilcef not in fold_tr(k.get("ilce") or ""):
            continue
        if cs_set is not None and k.get("calisma_sekli") not in cs_set:
            continue
        if it_set is not None and k.get("istihdam_turu") not in it_set:
            continue
        if dn_set is not None and k.get("deneyim") not in dn_set:
            continue
        if kpss is not None and k.get("kpss") is not kpss:
            continue  # None (bilinmiyor) iki filtrede de elenir — uydurma yok
        if qf:
            blob = fold_tr(f"{k.get('baslik', '')} {k.get('kurum', '')} {k.get('ozet', '')}")
            if qf not in blob:
                continue
        yeni = _yeni_mi(k.get("ilk_gorulme", ""), bugun, yeni_gun)
        if sadece_yeni and not yeni:
            continue
        out.append({**k, "yeni": yeni})
    out.sort(key=lambda x: x.get("tarih", ""), reverse=True)
    if sira == "son_basvuru_asc":
        # Son başvuru yaklaşan önce; tarihsizler en sonda
        out.sort(key=lambda x: (not x.get("son_basvuru"), x.get("son_basvuru") or ""))
    toplam = len(out)
    sayfa = max(1, sayfa)
    boyut = max(1, min(limit if limit != 20 else boyut, MAX_LIMIT))
    basla = (sayfa - 1) * boyut
    return out[basla:basla + boyut], toplam


class KariyerService:
    def meta(self) -> dict:
        kayitlar = _load()
        tarihler = sorted({k.get("tarih", "") for k in kayitlar if k.get("tarih")})
        kosu = {}
        try:
            p = Path(get_settings().project_root) / "data" / "processed" / "kariyer_kosu.json"
            if p.exists():
                kosu = json.load(open(p, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            kosu = {}
        return {
            "toplam": len(kayitlar),
            "kaynak_sayisi": len({k.get("kaynak", "") for k in kayitlar}),
            "son_tarih": tarihler[-1] if tarihler else "",
            "rehber_kaynak": len(_KAYNAKLAR),
            "son_kosu": kosu if isinstance(kosu, dict) else {},
        }

    def ilanlar(self, **kwargs) -> dict:
        sayfa = max(1, int(kwargs.pop("sayfa", 1) or 1))
        boyut = max(1, int(kwargs.pop("boyut", 20) or 20))
        limit = int(kwargs.get("limit", 20) or 20)
        eff = max(1, min(limit if limit != 20 else boyut, MAX_LIMIT))
        kayitlar, toplam = filtrele(_load(), sayfa=sayfa, boyut=boyut, **kwargs)
        return {"toplam": toplam, "sayfa": sayfa, "boyut": eff,
                "ilanlar": kayitlar}

    def kaynaklar(self, hat: str | None = None) -> dict:
        liste = [k for k in _KAYNAKLAR if not hat or k["hat"] == hat]
        return {"toplam": len(liste), "kaynaklar": liste}

    def bolumler(self) -> dict:
        """Bölüm seçici rehberi: etiket + o etiketteki kayıt sayısı."""
        say: dict[str, int] = {}
        for k in _load():
            for b in k.get("bolumler") or []:
                say[b] = say.get(b, 0) + 1
        liste = [{"id": bid, "label": label, "sayi": say.get(bid, 0)}
                 for bid, label in BOLUM_ETIKETLER.items()]
        return {"toplam": len(liste), "bolumler": liste}

    def filtreler(self) -> dict:
        """Facet: her filtrenin mevcut değerleri + sayıları (boş seçenek yok)."""
        say: dict[str, dict[str, int]] = {}
        for k in _load():
            for alan in ("hat", "bolge", "calisma_sekli", "istihdam_turu",
                         "deneyim", "kaynak"):
                v = k.get(alan) or ("Bilinmiyor" if alan == "bolge" else "bilinmiyor")
                say.setdefault(alan, {})
                say[alan][v] = say[alan].get(v, 0) + 1
            il = (k.get("il") or "").strip()
            if il:
                say.setdefault("il", {})
                say["il"][il] = say["il"].get(il, 0) + 1
        out = {alan: [{"id": v, "sayi": c} for v, c in
                      sorted(deger.items(), key=lambda x: -x[1])]
               for alan, deger in say.items()}
        # İl facet'lerine bölge ekle (kademeli seçim için)
        out["il"] = [{"id": v["id"], "sayi": v["sayi"],
                      "bolge": il_to_bolge(v["id"])} for v in out.get("il", [])]
        return out
