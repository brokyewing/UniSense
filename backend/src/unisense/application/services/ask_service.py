"""Ask service — RAG sorgu orkestrasyonu + sıra/puan intent routing."""
from __future__ import annotations

import hashlib
import re
import time
from functools import lru_cache
from typing import TYPE_CHECKING

from cachetools import TTLCache

from unisense.application.interfaces.llm_provider import LLMProvider
from unisense.application.services.retrieval_service import RetrievalService
from unisense.application.services.trend_service import has_history, trend_summary
from unisense.core.logging import get_logger
from unisense.domain.enums import ScoreType
from unisense.domain.models import Answer, Query, StudentProfile

if TYPE_CHECKING:
    from unisense.application.services.recommendation_service import RecommendationService

logger = get_logger(__name__)

# Cevap önbelleği — aynı sorgu (+ history + model) için Gemini'yi tekrar çağırmaktan kaçın.
# maxsize=512 ~5 MB civarı; ttl=3600 (1 saat) — guncel veri sınırı.
_response_cache: TTLCache[str, str] = TTLCache(maxsize=512, ttl=3600)


def _make_cache_key(query: Query, model_pref: str, user_context: dict | None = None) -> str:
    """Sorgu + top_k + history + model (+ profil puanları) → deterministic anahtar.

    user_context KPSS/DGS cevabını kişiselleştirir — anahtara girmezse bir
    kullanıcının puanına göre üretilen cevap başkasına servis edilir.
    """
    parts = [query.text.strip(), model_pref, str(getattr(query, "top_k", ""))]
    if user_context:
        parts.append(str(sorted(user_context.items())))
    if query.history:
        for t in query.history[-8:]:  # son 8 mesaj
            parts.append(f"{t.role}:{t.text.strip()}")
    raw = "|".join(parts).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:32]


# === Türkçe-güvenli lowercase ===
def _tr_lower(s: str) -> str:
    return s.replace("İ", "i").replace("I", "ı").lower()


# === Pattern'ler — sorgudan sıra/puan/uni türü/bölüm çıkar ===

# Sıralama patternleri (büyükten küçüğe spesiflik)
_RANK_PATTERNS = [
    # "300.000 sıra", "100.000 sıralama"
    (re.compile(r"(\d{1,3}\.\d{3})\b"),
     lambda m: int(m.group(1).replace(".", ""))),
    # "300 bin", "300bin", "100K", "300 k"
    (re.compile(r"\b(\d{1,3})\s*(?:bin|k)\b"),
     lambda m: int(m.group(1)) * 1000),
    # "50000 sıra", "12000 sıralama"
    (re.compile(r"\b(\d{4,7})\s*(?:sıra|sıralam|sıramla)"),
     lambda m: int(m.group(1))),
    # "rank 50000"
    (re.compile(r"\brank[\s:]*(\d{4,7})\b"),
     lambda m: int(m.group(1))),
]

# Puan patternleri
_SCORE_PATTERNS = [
    re.compile(r"\b(\d{3}(?:[.,]\d{1,3})?)\s*puan(?:la|ı|ım)?\b"),
    re.compile(r"\bpuanım[\s:]*(\d{3}(?:[.,]\d{1,3})?)\b"),
]

# Puan türü
_SCORE_TYPE_MAP = {
    "SAY":  [r"\bsay(ı|i)sal\b", r"\bsay\b", r"\bsayisal\b"],
    "EA":   [r"e(ş|s)it\s*a(ğ|g)(ı|i)rl(ı|i)k", r"\bea\b"],
    "SÖZ":  [r"\bs(ö|o)zel\b", r"\bs(ö|o)z\b"],
    "DİL":  [r"yabanc(ı|i)\s*dil", r"\bdil\b"],
    "TYT":  [r"\btyt\b"],
}

# Üniversite türü
_UNI_TYPE_PATTERNS = [
    (re.compile(r"\bdevlet\b"),         "Devlet"),
    (re.compile(r"\bvak(ı|i)f\b"),      "Vakıf"),
    (re.compile(r"\bkktc\b"),           "KKTC"),
    (re.compile(r"\byurt\s*d(ı|i)(ş|s)(ı|i)\b"), "YURTDISI"),
]

# Trend / yıllar arası sorgu pattern'i
_TREND_PATTERNS = [
    re.compile(r"\btrend"),
    re.compile(r"\b(y(ı|i)l|y(ı|i)llar)\s+(i(ç|c)inde|aras(ı|i))"),
    re.compile(r"\bge(ç|c)mi(ş|s)"),
    re.compile(r"\b(20\d\d)\s*[-–]\s*(20\d\d)"),  # "2020-2024"
    re.compile(r"y(ü|u)kseli|d(ü|u)(ş|s)(ü|u)"),  # "yükseliş/düşüş"
    re.compile(r"\bson\s+\d+\s+y(ı|i)l"),
]


# Coğrafi filtreler — Türkçe ekler için sondan \b kaldırıldı (prefix-match)
_GEO_PATTERNS = [
    # deniz, denizi, denizin, denize, sahili, kıyısında
    (re.compile(r"\b(deniz|sahil|k(ı|i)y(ı|i))"),                       "coastal"),
    # içerideki, içerde, iç kesim, kara
    (re.compile(r"\b(i(ç|c)\s*kesim|i(ç|c)er(de|ide)|kara\s*l)"),         "inland"),
    # merkez, merkezi, merkezindeki, şehir merkezi
    (re.compile(r"\b(merkez|(ş|s)ehir\s*merkezi)"),                       "central"),
    # metropol, metropolün, büyük şehir, büyükşehir
    (re.compile(r"\b(metropol|b(ü|u)y(ü|u)k\s*(ş|s)ehir)"),               "metropolis"),
    # karadeniz, karadenize, karadeniz'in
    (re.compile(r"\bkaradeniz"),                                          "sea_karadeniz"),
    (re.compile(r"\bmarmara"),                                            "sea_marmara"),
    (re.compile(r"\bege\b"),                                              "sea_ege"),  # ege kısa, \b sonda kalsın
    (re.compile(r"\bakdeniz"),                                            "sea_akdeniz"),
    (re.compile(r"\bbo(ğ|g)az\s*manzara"),                                "sea_marmara"),
]

# Şehir adından sonra gelebilecek ekler (fold'lu). Serbest önek eşleşmesi
# TUZAK: "bölüm"→"bolum" BOLU'yu, "karşı"→"karsi" KARS'ı yakalıyordu.
_CITY_SUFFIX = (r"(?:'?(?:da|de|ta|te|dan|den|tan|ten|daki|deki|taki|teki"
                r"|ya|ye|yi|yu|nin|nun|un|in|la|le|sinda|sinde))?\b")


# 81 il — sorgudan şehir tespiti için (geo.REGIONS'tan düzleştirilmiş)
def _city_patterns() -> list[tuple["re.Pattern[str]", str]]:
    from unisense.core.text import fold_tr
    from unisense.domain.geo import REGIONS

    pats = []
    for cities in REGIONS.values():
        for city in cities:
            # fold'lu anahtar: "sanliurfa" da "şanlıurfa" da yakalanır;
            # sadece bilinen ekler kabul — "bolum" BOLU değildir
            low = fold_tr(city)
            pats.append((re.compile(rf"\b{re.escape(low)}{_CITY_SUFFIX}"), city))
    return pats


_CITY_PATTERNS: list[tuple["re.Pattern[str]", str]] | None = None


# "X bölümü NEREDE/HANGİ üniversitede var?" kalıpları — bölüm tespit
# edildiyse şehir/üni olmasa da envanter listesi gerektirir (RAG'e gitmesin;
# vektör arama bu soruları üniversite-wiki mahallesine savurabiliyor)
_WHERE_PATTERNS = [
    re.compile(r"hangi\s+(ü|u)niversite"),
    re.compile(r"\bnerede\b|\bnerelerde\b|\bhangi\s+(ş|s)ehir"),
    re.compile(r"\bvar\s*m(ı|i)\b"),
    re.compile(r"\bbulunan\b|\bbulunuyor\b|\ba(ç|c)an\b"),
    re.compile(r"\blistele\b|\bt(ü|u)m(ü|u)n(ü|u)\b"),
]


@lru_cache(maxsize=1)
def _group_token_index() -> dict[str, list[str]]:
    """Bölüm grubu adlarının ayırt edici token index'i (fold'lu).

    'gastronomi' → ['Gastronomi ve Mutfak Sanatları'] gibi. Çok yaygın
    token'lar ('muhendisligi' ~80 grupta) index'e alınmaz — yanlış tetikler.
    """
    from unisense.application.services.compass_taxonomy import get_taxonomy
    from unisense.core.text import fold_tr

    tok_to_groups: dict[str, set[str]] = {}
    for g in get_taxonomy()["departments"]:
        for t in re.findall(r"[a-zçğıöşü]+", fold_tr(g["name"])):
            # Jenerik kelimeler sorgularda bölüm kastı olmadan geçer — index dışı
            # ("bilgi" → "Koç üniversitesi hakkında BİLGİ ver" tuzağı)
            if len(t) >= 4 and t not in {
                "bilim", "bilimleri", "yonetimi", "sanatlari", "bilgi",
                "genel", "temel", "uygulamali", "hizmetleri", "sistemleri",
                "teknolojisi", "teknolojileri", "tasarimi",
            }:
                tok_to_groups.setdefault(t, set()).add(g["name"])
    # ≤8 gruba işaret eden token'lar ayırt edici sayılır
    return {t: sorted(gs) for t, gs in tok_to_groups.items() if len(gs) <= 8}


# Yaygın bölüm anahtar kelimeleri (kısmi eşleşme için)
_DEPT_KEYWORDS = [
    "tıp", "diş", "eczacılık", "hemşirelik", "fizyoterapi", "veteriner",
    "bilgisayar mühendis", "yazılım mühendis", "yapay zeka", "veri bilim",
    "elektrik", "elektronik", "makine", "endüstri mühendis", "inşaat",
    "kimya mühendis", "biyomedikal", "havacılık", "uçak", "uzay", "otomotiv",
    "mimarlık", "iç mimarlık", "tasarım",
    "hukuk", "psikoloji", "sosyoloji", "felsefe",
    "iktisat", "işletme", "maliye", "muhasebe", "bankacılık", "pazarlama",
    "öğretmenlik", "eğitim",
    "matematik", "fizik", "biyoloji",
    "gazetecilik", "halkla ilişkiler", "iletişim",
    "ilahiyat",
]


def _extract_intent(query: str) -> dict | None:
    """Sorgudan sıra/puan/şehir/üni/bölüm intent'i çıkar.

    Return:
        None  → yapılandırılmış veri gerektirmeyen sorgu (saf RAG kullan)
        dict  → {rank?, score?, score_type, uni_types, departments,
                 cities, universities, geo_flags}
    Tetikleyiciler: sıra/puan VEYA coğrafi filtre VEYA (bölüm + şehir/üni)
    — "İstanbul'daki tıp fakülteleri kaç puan?" tarzı envanter soruları
    RAG'in top_k limitine takılır, yapısal listeleme gerekir.
    """
    q = _tr_lower(query)

    # Sıralama
    rank = None
    for pat, fn in _RANK_PATTERNS:
        m = pat.search(q)
        if m:
            try:
                rank = fn(m)
                break
            except (ValueError, IndexError):
                pass

    # Puan
    score = None
    for pat in _SCORE_PATTERNS:
        m = pat.search(q)
        if m:
            try:
                score = float(m.group(1).replace(",", "."))
                # Geçerli aralık: 100-600
                if not (100 <= score <= 600):
                    score = None
                break
            except (ValueError, IndexError):
                pass

    # Coğrafi flagler — sıra/puan olmadan da bunlar yakalanabilir
    geo_flags: list[str] = []
    for pat, label in _GEO_PATTERNS:
        if pat.search(q):
            geo_flags.append(label)

    # Şehir + bölüm eşleşmeleri fold'lu yapılır — kullanıcı "istanbul tip"
    # yazsa da (ASCII) "İstanbul tıp" yazsa da yakalanır
    from unisense.core.text import fold_tr

    qf = fold_tr(query)

    # Şehirler (81 il, ek almış halleriyle)
    global _CITY_PATTERNS
    if _CITY_PATTERNS is None:
        _CITY_PATTERNS = _city_patterns()
    cities: list[str] = []
    for pat, city in _CITY_PATTERNS:
        if pat.search(qf):
            cities.append(city)

    # Bölüm anahtar kelimeleri (fold'lu kıyas, orijinal kw döner)
    departments: list[str] = []
    for kw in _DEPT_KEYWORDS:
        if fold_tr(kw) in qf:
            departments.append(kw)

    # Taksonomi-tabanlı bölüm tespiti: sorgudaki ayırt edici kelimeler
    # ("gastronomi", "odyoloji"...) 604 grup adına karşı denenir — sabit
    # keyword listesinin kapsamadığı tüm bölümleri yakalar
    token_index = _group_token_index()
    q_words = set(re.findall(r"[a-zçğıöşü]+", qf))
    for w in q_words:
        if w in token_index and w not in [fold_tr(k) for k in departments]:
            departments.append(w)

    # "Nerede / hangi üniversitede / var mı" kalıbı
    is_where_query = any(p.search(q) or p.search(qf) for p in _WHERE_PATTERNS)

    # Üniversite adları (Hacettepe, Boğaziçi... — veri destekli, cache'li)
    universities: list[str] = []
    try:
        from unisense.application.services.recommendation_service import detect_universities
        universities = detect_universities(query)
    except Exception:  # noqa: BLE001 — veri dosyası yoksa (test ortamı) sessiz geç
        pass

    has_listing_target = departments and (cities or universities or is_where_query)
    if rank is None and score is None and not geo_flags and not has_listing_target:
        return None

    # Puan türü
    score_type = "SAY"  # default
    for st, pats in _SCORE_TYPE_MAP.items():
        if any(re.search(p, q) for p in pats):
            score_type = st
            break

    # Üniversite türü
    uni_types: list[str] = []
    for pat, label in _UNI_TYPE_PATTERNS:
        if pat.search(q):
            uni_types.append(label)

    return {
        "rank": rank,
        "score": score,
        "score_type": score_type,
        "uni_types": uni_types,
        "departments": departments,
        "cities": cities,
        "universities": universities,
        "geo_flags": geo_flags,
    }


def _build_listing_context(intent: dict, rec_service: "RecommendationService") -> str:
    """Sıra/puan VERİLMEDEN sorulan envanter soruları için program listesi.

    Örn: "İstanbul'daki tıp fakülteleri kaç puan, kontenjan kaç?"
    RAG top_k=12 ile ~98 programın tamamını getiremez; yapısal veriden
    eksiksiz liste + toplam kontenjan üretilir.
    """
    result = rec_service.list_programs(
        cities=intent.get("cities") or None,
        uni_codes=intent.get("universities") or None,
        dept_keywords=intent.get("departments") or None,
        limit=30,
    )
    if not result["total"]:
        return ""

    scope = []
    if intent.get("cities"):
        scope.append("/".join(intent["cities"]))
    if intent.get("universities"):
        scope.append(f"{len(intent['universities'])} üniversite")
    scope.append(", ".join(intent.get("departments") or []))

    lines = [f"=== PROGRAM LİSTESİ ({' — '.join(s for s in scope if s)}) — 2025 verisi ==="]
    lines.append(
        f"Toplam {result['total']} program, toplam kontenjan {result['total_quota']:,}. "
        f"(İlk {len(result['programs'])} tanesi taban sırasına göre listelendi)"
    )
    for p in result["programs"]:
        rank_s = f"{p['base_rank']:,}" if p["base_rank"] else "?"
        score_s = f"{p['base_score']:.2f}" if p["base_score"] else "?"
        # Burs bilgisi bölüm adında zaten varsa tekrarlama
        burs = ""
        if p.get("scholarship") and p["scholarship"] not in p["department_name"]:
            burs = f" ({p['scholarship']})"
        uni = p["university_name"]
        city = "" if p["city"] and p["city"] in uni else f" ({p['city']})"
        lines.append(
            f"• [{p['department_code']}] {p['department_name']}{burs} — {uni}{city} "
            f"sıra: {rank_s} | taban: {score_s} | kontenjan: {p['quota'] or '?'}"
        )
    return "\n".join(lines)


# === KPSS / DGS sorgu yönlendirmesi ===
# DİKKAT: tek başına "kadro" YKS bağlamında da geçer ("akademik kadro") —
# sadece kpss/memur/atanma kelimeleri yönlendirir
_KPSS_RE = re.compile(r"\bkpss\b|\bmemur(lug|luk|iyet|u|a)?\b|\batan(ma|abilir|(ı|i)r(ı|i)m)", re.I)
# Sınav adı geçmeyen genel yerleştirme soruları — kullanıcının profil
# yolu (exam_track) DGS/KPSS ise o kanala yönlendirilir
_GENERIC_PLACEMENT_RE = re.compile(
    r"nereye\s+(girebilir|yerle(ş|s))|hangi\s+(b(ö|o)l(ü|u)m|program|kadro)|"
    r"\byerle(ş|s)(ebilir|irim|me)\b|puan(ı|i)mla", re.I)
_DGS_RE = re.compile(r"\bdgs\b|dikey\s*ge(ç|c)i(ş|s)", re.I)
_KPSS_PUAN_RE = re.compile(r"\b(\d{2,3}(?:[.,]\d{1,3})?)\s*(?:kpss\s*)?puan")


def _build_kpss_context(query: str, user_context: dict | None = None) -> str:
    """KPSS sorusu → aktif dönem kadroları + geçmiş tabanlarla context."""
    from unisense.core.di import get_kpss_service
    from unisense.core.text import fold_tr

    uc = user_context or {}
    qf = fold_tr(query)
    # Puan: önce sorgudan, yoksa profilden (KPSS aralığı 40-105)
    puan = uc.get("kpss_puan")
    m = _KPSS_PUAN_RE.search(qf)
    if m:
        v = float(m.group(1).replace(",", "."))
        if 40 <= v <= 105:
            puan = v
    # Bölüm: taksonomi token'ları
    bolum = ""
    token_index = _group_token_index()
    for w in re.findall(r"[a-zçğıöşü]+", fold_tr(query)):
        if w in token_index:
            bolum = w
            break
    duzey = ("önlisans" if "onlisans" in qf or "on lisans" in qf
             else "ortaöğretim" if "ortaogretim" in qf or "lise" in qf
             else uc.get("kpss_duzey") or "lisans")

    r = get_kpss_service().kadro_ara(bolum=bolum, puan=puan, duzey=duzey, limit=15)
    lines = ["=== KPSS 2026/1 AKTİF TERCİH DÖNEMİ KADROLARI (tercih: 9-16 Temmuz) ===",
             f"Filtre: düzey={duzey}, bölüm={bolum or 'tümü'}, puan={puan or '?'}",
             f"Uyan kadro sayısı: {r['total']} (ilk 15 gösteriliyor)", ""]
    for it in r["items"]:
        taban = f"geçen dönem taban {it['gecmis_taban']:.2f}" if it["gecmis_taban"] else "geçmiş taban yok"
        lines.append(f"• [{it['kadro_kodu']}] {it['unvan']} — {it['kurum']} ({it['il']}) "
                     f"kontenjan {it['kontenjan']}, {taban}, {it['eslesme']}")
    lines.append("")
    lines.append("NOT: B grubu merkezi yerleştirme kadroları. A grubu (uzman yrd/müfettiş) "
                 "kurum sınavlarıyla alınır, bu listede olmaz. " + r["uyari"])
    return "\n".join(lines)


def _build_dgs_context(query: str, user_context: dict | None = None) -> str:
    """DGS sorusu → puana uygun lisans programları context'i."""
    from unisense.core.di import get_dgs_service
    from unisense.core.text import fold_tr

    uc = user_context or {}
    qf = fold_tr(query)
    puan = uc.get("dgs_puan")
    for m in re.finditer(r"\b(\d{3}(?:[.,]\d{1,3})?)\b", qf):
        v = float(m.group(1).replace(",", "."))
        if 140 <= v <= 500:
            puan = v
            break
    pt = ("EA" if re.search(r"\bea\b|esit", qf)
          else "SÖZ" if re.search(r"\bsoz(el)?\b", qf)
          else "SAY" if re.search(r"\bsay(isal)?\b", qf)
          else uc.get("dgs_turu") or "SAY")
    bolum = ""
    token_index = _group_token_index()
    for w in re.findall(r"[a-zçğıöşü]+", fold_tr(query)):
        if w in token_index:
            bolum = w
            break

    r = get_dgs_service().program_ara(puan_turu=pt, puan=puan, bolum=bolum, limit=15)
    lines = ["=== DGS LİSANS GEÇİŞ PROGRAMLARI (2025 tabanları) ===",
             f"Filtre: puan türü={pt}, puan={puan or '?'}, bölüm={bolum or 'tümü'}",
             f"Uyan program sayısı: {r['total']} (ilk 15)", ""]
    for it in r["items"]:
        taban = f"taban {it['min_puan']:.2f}" if it["min_puan"] else "geçen yıl boş"
        lines.append(f"• [{it['department_code']}] {it['program_adi']} ({it['city']}) "
                     f"— {taban}, kontenjan {it['kontenjan']}")
    lines.append("")
    lines.append(r["uyari"])
    return "\n".join(lines)


def _build_recommendation_context(intent: dict, rec_service: "RecommendationService") -> str:
    """Intent → recommendation servisi → kısa context string."""
    # Sıra/puan yoksa bu bir envanter sorusu — kişisel öneri yerine liste dön
    if intent.get("rank") is None and intent.get("score") is None:
        listing = _build_listing_context(intent, rec_service)
        if listing:
            return listing
        # Liste boş döndüyse (filtre tutmadı) normal akışa düş

    try:
        st_enum = ScoreType(intent["score_type"]) if isinstance(intent["score_type"], str) else intent["score_type"]
    except ValueError:
        st_enum = ScoreType.SAY

    profile = StudentProfile(
        score_type=st_enum,
        score=intent.get("score"),
        rank=intent.get("rank"),
        preferred_cities=intent.get("cities") or [],
        preferred_uni_types=intent.get("uni_types") or [],
        preferred_departments=intent.get("departments") or [],
    )
    # Geo flagleri profile attach et — RecommendationService bunları okuyacak
    geo_flags = intent.get("geo_flags") or []
    setattr(profile, "_geo_flags", geo_flags)
    result = rec_service.recommend(profile)

    lines = ["=== TERCİH ÖNERİLERİ (sıra bazlı, taban verisi 2025) ==="]
    lines.append(f"Profil: {st_enum.value}, sıra={intent.get('rank') or '?'}, puan={intent.get('score') or '?'}")
    if intent.get("uni_types"):
        lines.append(f"Filtre: {', '.join(intent['uni_types'])}")
    if intent.get("departments"):
        lines.append(f"Bölüm: {', '.join(intent['departments'])}")
    if geo_flags:
        lines.append(f"Coğrafi filtre: {', '.join(geo_flags)}")
    lines.append(f"Notes: {result.notes}")
    lines.append("")

    for cat_name, cat_list in [
        ("GÜVENLİ (rahat yerleşir)", result.safe[:8]),
        ("HEDEF (uygun)", result.target[:10]),
        ("ÜST SEVİYE (zorlama)", result.reach[:5]),
    ]:
        if not cat_list:
            continue
        lines.append(f"--- {cat_name} ---")
        for r in cat_list:
            rank_s = f"{r.last_year_base_rank:,}" if r.last_year_base_rank else "?"
            score_s = f"{r.last_year_base_score:.2f}" if r.last_year_base_score else "?"
            lines.append(
                f"• [{r.department_code}] {r.department_name} — {r.university_name} ({r.city}) "
                f"sıra: {rank_s} | taban: {score_s}"
            )
        lines.append("")

    return "\n".join(lines)


class AskService:
    """RAG (Gemini + ChromaDB) + sıra/puan intent → Recommend hybrid."""

    def __init__(
        self,
        retrieval: RetrievalService,
        llm: LLMProvider,
        recommendation: "RecommendationService | None" = None,
    ) -> None:
        self._retrieval = retrieval
        self._llm = llm
        self._recommendation = recommendation

    def execute(self, query: Query, user_context: dict | None = None) -> Answer:
        start = time.perf_counter()

        # 0. Cache check — aynı sorgu+history+model son 1 saat içinde cevaplanmış mı?
        model_pref = getattr(query, "model_preference", None) or "gemini"
        cache_key = _make_cache_key(query, model_pref, user_context)
        cached_text = _response_cache.get(cache_key)
        if cached_text is not None:
            # Cache'de cevap var — retrieval yine yap (frontend kaynak chunk'larını bekliyor),
            # ama LLM çağırma. Toplam latency ~50-300ms.
            docs = self._retrieval.retrieve(query)
            total_ms = int((time.perf_counter() - start) * 1000)
            logger.info("ask_cache_hit", cache_key=cache_key[:8], total_ms=total_ms)
            return Answer(
                query=query.text,
                text=cached_text,
                docs=docs,
                total_latency_ms=total_ms,
            )

        # 0b. KPSS / DGS sorguları — kendi yapısal veri kaynaklarına yönlenir
        # (YKS RAG'i bu soruları cevaplayamaz; kadro/geçiş verisi ayrı)
        sinav_context = ""
        uc_track = (user_context or {}).get("exam_track")
        try:
            if _KPSS_RE.search(query.text):
                sinav_context = _build_kpss_context(query.text, user_context)
                logger.info("kpss_intent_routed")
            elif _DGS_RE.search(query.text):
                sinav_context = _build_dgs_context(query.text, user_context)
                logger.info("dgs_intent_routed")
            elif uc_track == "KPSS" and _GENERIC_PLACEMENT_RE.search(query.text):
                # Sınav adı yazılmamış ama kullanıcının yolu KPSS
                sinav_context = _build_kpss_context(query.text, user_context)
                logger.info("kpss_intent_routed", via="exam_track")
            elif uc_track == "DGS" and _GENERIC_PLACEMENT_RE.search(query.text):
                sinav_context = _build_dgs_context(query.text, user_context)
                logger.info("dgs_intent_routed", via="exam_track")
        except Exception as e:  # noqa: BLE001
            logger.warning("sinav_context_failed", error=str(e)[:200])

        # 1. Intent kontrolü — sıra/puan tabanlı sorgu mu?
        intent = _extract_intent(query.text) if not sinav_context else None
        rec_context = ""
        if intent and self._recommendation is not None:
            try:
                rec_context = _build_recommendation_context(intent, self._recommendation)
                logger.info(
                    "intent_routed",
                    rank=intent.get("rank"),
                    score=intent.get("score"),
                    score_type=intent.get("score_type"),
                    uni_types=intent.get("uni_types"),
                    departments=intent.get("departments"),
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("intent_build_failed", error=str(e)[:200])

        # 2. Retrieval (RAG chunks)
        docs = self._retrieval.retrieve(query)
        rag_context = self._retrieval.build_context(docs)

        # 2b. Trend tespiti — kullanıcı "yıllar içinde / trend / geçmiş" sorduysa
        # ve retrieval'da program chunk'ı varsa, çoklu yıl trend özeti ekle
        trend_context = ""
        q_lower = _tr_lower(query.text)
        is_trend_query = any(p.search(q_lower) for p in _TREND_PATTERNS)
        if is_trend_query:
            program_codes_in_docs = list({d.department_code for d in docs if d.department_code})[:5]
            trend_lines = []
            for code in program_codes_in_docs:
                summary = trend_summary(code)
                if summary:
                    trend_lines.append(f"[{code}] {summary}")
            if trend_lines:
                trend_context = "=== ÇOKLU YIL TREND ===\n" + "\n\n".join(trend_lines)
                logger.info("trend_context_added", programs=len(trend_lines))
            elif not has_history():
                # History dosyası yoksa kullanıcıya açık not
                trend_context = (
                    "=== TREND NOTU ===\n"
                    "Şu anda 2025 verisi var. Geçmiş yıl arşivi (2020-2024) hazırlanıyor — "
                    "trend sorularına şu an cevap için Wikipedia/üni sayfalarındaki sözel "
                    "bilgilerle yetinin."
                )

        # 3. Context'i birleştir — sınav (KPSS/DGS), recommendation, trend, RAG
        parts = []
        if sinav_context:
            parts.append(sinav_context)
        if rec_context:
            parts.append(rec_context)
        if trend_context:
            parts.append(trend_context)
        if rag_context:
            parts.append("=== EK RAG KAYNAKLARI ===\n" + rag_context)
        context = "\n\n".join(parts) if parts else rag_context

        # 4. LLM cevabı (multi-turn destekli — history varsa)
        history_dicts = []
        if query.history:
            for t in query.history:
                history_dicts.append({"role": t.role, "text": t.text})

        text = ""
        llm_ok = False
        try:
            text = self._llm.generate(
                query.text,
                context=context,
                history=history_dicts if history_dicts else None,
            )
            llm_ok = True
        except Exception as e:  # noqa: BLE001
            logger.warning("llm_failed", error=str(e)[:200])
            text = f"⚠️ Şu an cevap üretemedim: {str(e)[:120]}"

        # Cevabı önbelleğe yaz (sadece başarılı LLM cevabı için, hata mesajını cache'leme)
        if llm_ok and text:
            _response_cache[cache_key] = text

        total_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "ask_completed",
            query_len=len(query.text),
            docs=len(docs),
            has_recommendation=bool(rec_context),
            total_ms=total_ms,
            cache_size=len(_response_cache),
        )

        return Answer(
            query=query.text,
            text=text,
            docs=docs,
            total_latency_ms=total_ms,
        )
