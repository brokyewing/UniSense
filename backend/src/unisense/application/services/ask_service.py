"""Ask service — RAG sorgu orkestrasyonu + sıra/puan intent routing."""
from __future__ import annotations

import hashlib
import re
import time
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


def _make_cache_key(query: Query, model_pref: str) -> str:
    """Sorgu + top_k + history + model tercihinden deterministic anahtar üret."""
    parts = [query.text.strip(), model_pref, str(getattr(query, "top_k", ""))]
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

# 81 il — sorgudan şehir tespiti için (geo.REGIONS'tan düzleştirilmiş)
def _city_patterns() -> list[tuple["re.Pattern[str]", str]]:
    from unisense.domain.geo import REGIONS

    pats = []
    for cities in REGIONS.values():
        for city in cities:
            low = _tr_lower(city)
            # "istanbul", "istanbul'da", "istanbuldaki" — ek almış halleri de yakala
            pats.append((re.compile(rf"\b{re.escape(low)}"), city))
    return pats


_CITY_PATTERNS: list[tuple["re.Pattern[str]", str]] | None = None


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

    # Şehirler (81 il, ek almış halleriyle)
    global _CITY_PATTERNS
    if _CITY_PATTERNS is None:
        _CITY_PATTERNS = _city_patterns()
    cities: list[str] = []
    for pat, city in _CITY_PATTERNS:
        if pat.search(q):
            cities.append(city)

    # Bölüm anahtar kelimeleri
    departments: list[str] = []
    for kw in _DEPT_KEYWORDS:
        if kw in q:
            departments.append(kw)

    # Üniversite adları (Hacettepe, Boğaziçi... — veri destekli, cache'li)
    universities: list[str] = []
    try:
        from unisense.application.services.recommendation_service import detect_universities
        universities = detect_universities(query)
    except Exception:  # noqa: BLE001 — veri dosyası yoksa (test ortamı) sessiz geç
        pass

    has_listing_target = departments and (cities or universities)
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

    def execute(self, query: Query) -> Answer:
        start = time.perf_counter()

        # 0. Cache check — aynı sorgu+history+model son 1 saat içinde cevaplanmış mı?
        model_pref = getattr(query, "model_preference", None) or "gemini"
        cache_key = _make_cache_key(query, model_pref)
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

        # 1. Intent kontrolü — sıra/puan tabanlı sorgu mu?
        intent = _extract_intent(query.text)
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

        # 3. Context'i birleştir — recommendation, sonra trend, sonra RAG
        parts = []
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
