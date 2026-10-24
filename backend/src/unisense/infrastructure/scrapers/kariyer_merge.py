"""Kariyer merge & deduplication — şema v2 migrasyon, çapraz kaynak tekilleştirme, 30 günlük kayan pencere."""
from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

from unisense.core.text import fold_tr
from unisense.domain.geo import il_ilce_ayikla, il_to_bolge, metinden_il_bul

OUT = Path(__file__).resolve().parents[4] / "data" / "processed" / "kariyer_ilanlar.json"
KOSU_DOSYA = Path(__file__).resolve().parents[4] / "data" / "processed" / "kariyer_kosu.json"

SAKLA_GUN = 30  # kayan pencere: daha eskiler _merge'de budanır


def _tarih_iso(ham: str | None, bugun: str) -> str:
    """RFC-822 / ISO / epoch → YYYY-MM-DD. Parse edilemezse bugün."""
    if not ham:
        return bugun
    # Önce ISO formatını dene (2026-08-15, 2026-09-01T10:00:00Z, etc.)
    try:
        # "2026-08-15" veya "2026-09-01T10:00:00Z" formatları
        if "T" in ham:
            dt = datetime.fromisoformat(ham)
            return dt.date().isoformat()
        # Sadece tarih kısmı (YYYY-MM-DD)
        if len(ham) >= 10 and ham[4] == "-" and ham[7] == "-":
            return ham[:10]
    except Exception:
        pass
    # Son olarak RFC-822 dene (Careerjet: "Wed, 29 Jun 2026 10:00:00 GMT")
    try:
        dt = parsedate_to_datetime(ham)
        return dt.date().isoformat()
    except Exception:
        return bugun


# === Şema v2 ===
KAYNAK_KOD = {"Jooble": "jooble", "Careerjet": "careerjet", "Resmî Gazete": "rg",
              "kamuilan.sbb.gov.tr": "kamuilan", "Kariyer Kapısı": "kariyerkapisi",
              "AkademikTR": "akademiktr", "ilan.gov.tr": "ilangovtr",
              "Savunma Kariyer": "savunmakariyer", "TÜRKSAT Kariyer": "turksat"}

V2_BILINMIYOR = "bilinmiyor"


def _v2_id(kayit: dict) -> str:
    eski = str(kayit.get("id") or "")
    if ":" in eski:
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
    ham_konum = (k.get("il") or k.get("sehir") or "").strip()
    il, ilce, bolge = il_ilce_ayikla(ham_konum)
    if not il:
        il = metinden_il_bul(k.get("kurum")) or metinden_il_bul(k.get("baslik"))
        bolge = il_to_bolge(il) if il else "Bilinmiyor"
    k["il"] = il or ""
    k["ilce"] = (k.get("ilce") or ilce or "").strip()
    k["bolge"] = bolge

    _fold_cs = fold_tr(f"{k.get('baslik', '')} {k.get('ozet', '')}")
    _cs_kaynak = ("kaynak" if k.get("calisma_sekli") not in (None, "", V2_BILINMIYOR)
                  else _calisma_sekli_kaynak(_fold_cs, k.get("hat")))
    if not k.get("calisma_sekli") or k.get("calisma_sekli") == V2_BILINMIYOR:
        k["calisma_sekli"] = _calisma_sekli(_fold_cs)
        if k["calisma_sekli"] == V2_BILINMIYOR and k.get("hat") == "kamu":
            k["calisma_sekli"] = "yuzyuze"
    if k["calisma_sekli"] != V2_BILINMIYOR:
        k.setdefault("detay", {})
        if isinstance(k["detay"], dict):
            k["detay"]["calisma_sekli_kaynak"] = _cs_kaynak
    if k.get("kpss") is None:
        var_mi, tur = _kpss_bilgi(fold_tr(f"{k.get('baslik', '')} {k.get('ozet', '')}"))
        k["kpss"] = var_mi
        if tur:
            det = dict(k.get("detay") or {})
            det.setdefault("kpss_tur", tur)
            k["detay"] = det
    if not k.get("istihdam_turu") or k["istihdam_turu"] == V2_BILINMIYOR:
        k["istihdam_turu"] = _istihdam_turu_metinden((k.get("detay") or {}).get("tur"))
    k.setdefault("istihdam_turu", V2_BILINMIYOR)
    k.setdefault("deneyim", V2_BILINMIYOR)
    k.setdefault("pozisyon_etiket", [])
    return k


def _migrate(kayitlar: list[dict]) -> list[dict]:
    """Tüm kayıtları v2'ye taşır (id, kaynak_kod, il/ilce/bolge, calisma_sekli_kaynak)."""
    return [v2_kayit(k) for k in kayitlar]


def _anahtar(k: dict) -> str | None:
    """Tekilleştirme anahtarı: kaynak_kod + link/başlık hash."""
    if not k.get("url"):
        return None
    kod = k.get("kaynak_kod") or k.get("kaynak") or "diger"
    url = k.get("url") or ""
    return f"{kod}:{hashlib.sha1(url.encode()).hexdigest()[:12]}"


def _dedup_capraz(kayitlar: list[dict]) -> tuple[list[dict], int]:
    """Çapraz kaynak tekilleştirme: aynı link farklı kaynaklardan gelirse biri kalır (kamu öncelikli)."""
    oncelik = {"kamu": 0, "ozel": 1}
    gruplar: dict[str, list[dict]] = {}
    for k in kayitlar:
        ak = _anahtar(k)
        if ak:
            gruplar.setdefault(ak, []).append(k)

    birlesik = []
    silinen = 0
    for ak, lst in gruplar.items():
        if len(lst) == 1:
            birlesik.append(lst[0])
        else:
            lst.sort(key=lambda x: oncelik.get(x.get("hat"), 2))
            birlesik.append(lst[0])
            silinen += len(lst) - 1
    return birlesik, silinen


def _tr_tarih(gun: str, ay: str, bugun: date) -> str:
    """Tarih stringi -> YYYY-MM-DD (eski format desteği)."""
    try:
        return f"{int(gun):04d}-{int(ay):02d}-01"  # sadece yıl-ay
    except Exception:
        return bugun


def _kosu_raporu(yeni: list[dict], eski_idler: set[str],
                 bugun: str) -> dict[str, int]:
    """Kosra yapılan çekimlerin özeti."""
    cekilen: dict[str, int] = {}
    for k in yeni:
        kay = k.get("kaynak") or k.get("kaynak_kod") or "diger"
        cekilen[kay] = cekilen.get(kay, 0) + 1
    return cekilen


def _gecmis_guncelle(kosu_dosya: Path, bugun: str, cekilen: dict[str, int]) -> tuple[list[dict], list[str]]:
    """kosu_dosya JSON'ını günceller, (eski_kayitlar, eski_idler) döner."""
    eski: list[dict] = []
    eski_idler: set[str] = set()
    if kosu_dosya.exists():
        try:
            eski = json.loads(kosu_dosya.read_text(encoding="utf-8"))
            eski_idler = {k.get("id") for k in eski if k.get("id")}
        except Exception:
            eski = []
            eski_idler = set()

    # 30 günlük pencere: bugünden SAKLA_GUN öncesi sil
    from datetime import timedelta
    esik = date.fromisoformat(bugun) - timedelta(days=SAKLA_GUN)

    guncel = []
    for k in eski:
        tid = k.get("tarih") or k.get("ilk_gorulme")
        if tid:
            try:
                tdate = date.fromisoformat(tid[:10])
                if tdate >= esik:
                    guncel.append(k)
            except Exception:
                guncel.append(k)
        else:
            guncel.append(k)

    kosu_dosya.write_text(json.dumps(guncel, ensure_ascii=False, indent=2), encoding="utf-8")
    return guncel, list(eski_idler)


def _merge(yeni: list[dict], eski: list[dict], ref_date: date | None = None) -> list[dict]:
    """Yeni + eski → birleştir, çapraz tekilleştir, 30 gün penceresi, v2 migrasyon.

    Budama mantığı (GOREVLER.md'ye göre):
    1. son_basvuru VARSA ve GELECEKTEYSE → KALIR (budama yok)
    2. son_basvuru VARSA ve GEÇMİŞTEYSE → 7 gün tolerans içindeyse KALIR, aksi budanır
    3. son_basvuru YOKSA → 30 günlük yaş budaması (tarih/ilk_gorulme bazlı)
    """
    # 1) Eski v1 → v2
    eski_v2 = _migrate(eski)

    # 2) Birleştir
    birlesik = eski_v2 + yeni

    # 3) Çapraz kaynak tekilleştirme
    birlesik, sil = _dedup_capraz(birlesik)

    # 4) Budama
    from datetime import timedelta
    ref = ref_date or date.today()
    esik = ref - timedelta(days=SAKLA_GUN)
    guncel = []
    for k in birlesik:
        son_basvuru = k.get("son_basvuru")
        if son_basvuru:
            # son_basvuru VAR → gelecekteyse KALIR, geçmişteyse 7 gün tolerans
            try:
                t = date.fromisoformat(son_basvuru[:10])
                if t >= ref:  # son_basvuru bugün veya gelecekte
                    guncel.append(k)
                    continue
                # geçmişte → 7 gün tolerans kontrolü
                if t >= ref - timedelta(days=7):
                    guncel.append(k)
                    continue
                # 7 günden eski geçmiş → budanır
            except Exception:
                pass  # parse edilemezse yaş budamasına düş
        # son_basvuru YOK veya parse edilemedi → yaş budaması (30 gün)
        ref_str = k.get("ilk_gorulme") or k.get("tarih")
        if ref_str:
            try:
                t = date.fromisoformat(ref_str[:10])
                if t >= esik:
                    guncel.append(k)
                continue
            except Exception:
                pass
        guncel.append(k)  # tarih yoksa da koru

    print(f"  Merge: eski={len(eski_v2)}, yeni={len(yeni)}, birlesik={len(birlesik)}, son={len(guncel)}, silinen={sil}")
    return guncel


# === Yardımcı fonksiyonlar (kariyer_scraper'dan taşındı) ===

# Bölüm anahtarları ÖNceden fold'lu (ascii) yazılır; metin fold_tr ile eşleşir.
# Kaynak: PDF nitelik kodları (4531/4533/4611) + yaygın mühendislik bölümleri.
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
    etiketler = set()
    for bolum, anahtarlar in BÖLÜM_ANAHTAR.items():
        for kw in anahtarlar:
            if kw in metin_fold:
                etiketler.add(bolum)
                break
    return sorted(etiketler)


def _calisma_sekli(metin_fold: str) -> str:
    # 1. Açık beyan (online/hibrit/yuzyuze)
    if any(k in metin_fold for k in ("uzaktan", "remote", "home office", "evden calis", "e-uzaktan", "tam uzaktan")):
        return "online"
    if any(k in metin_fold for k in ("hibrit", "hybrid", "yarim uzaktan", "esnek calisma")):
        return "hibrit"
    if any(k in metin_fold for k in ("yuz yuze", "yüz yüze", "on site", "ofis", "ofiste", "calisma alani", "is yerinde")):
        return "yuzyuze"
    # 2. Dolaylı sinyaller (mağaza/fabrika/şube/depo/iş yeri) → yuzyuze
    if any(k in metin_fold for k in ("magaza", "mağaza", "fabrika", "santiye", "depo", "sube", "şube",
                                     "calisma alani", "is yerinde", "isyerinde")):
        return "yuzyuze"
    return "bilinmiyor"


def _calisma_sekli_kaynak(fold_metin: str, hat: str | None) -> str:
    """Çalışma şekli kaynağını belirle: kaynak | beyan | dolayli | varsayim."""
    # Doğrudan beyan var mı?
    if any(k in fold_metin for k in ("uzaktan", "remote", "home office", "evden calis", "e-uzaktan", "tam uzaktan",
                                     "hibrit", "hybrid", "yarim uzaktan", "esnek calisma",
                                     "yuz yuze", "yüz yüze", "on site", "ofis", "ofiste", "calisma alani", "is yerinde")):
        return "beyan"
    # Dolaylı sinyaller (mağaza/fabrika/şantiye)
    if any(k in fold_metin for k in ("magaza", "mağaza", "fabrika", "santiye", "depo", "sube", "şube",
                                     "ofis", "ofiste", "calisma alani", "is yerinde", "isyerinde")):
        return "dolayli"
    # Kamu varsayımı
    if hat == "kamu":
        return "varsayim"
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


def _kpss_bilgi(fold_metin: str) -> tuple[bool | None, str | None]:
    if "kpss" not in fold_metin:
        return None, None
    if "kpss 90" in fold_metin or "kpss 80" in fold_metin:
        return True, "B"
    if "kpss 70" in fold_metin or "kpss 60" in fold_metin:
        return True, "B"
    return True, None


if __name__ == "__main__":
    # Test için
    print("kariyer_merge module loaded")