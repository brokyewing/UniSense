"""Ask service — RAG sorgu orkestrasyonu + sıra/puan intent routing."""
from __future__ import annotations

import re
import time
from typing import TYPE_CHECKING

from unisense.application.interfaces.llm_provider import LLMProvider
from unisense.application.services.retrieval_service import RetrievalService
from unisense.application.services.trend_service import has_history, trend_summary
from unisense.core.logging import get_logger
from unisense.domain.enums import ScoreType
from unisense.domain.models import Answer, Query, StudentProfile

if TYPE_CHECKING:
    from unisense.application.services.recommendation_service import RecommendationService

logger = get_logger(__name__)


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
    """Sorgudan sıra/puan/üni-türü/bölüm intent'i çıkar.

    Return:
        None  → bu sorgu sıra/puan tabanlı değil (saf RAG kullan)
        dict  → {rank?, score?, score_type, uni_types: [...], departments: [...]}
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

    if rank is None and score is None and not geo_flags:
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

    # Bölüm anahtar kelimeleri
    departments: list[str] = []
    for kw in _DEPT_KEYWORDS:
        if kw in q:
            departments.append(kw)

    return {
        "rank": rank,
        "score": score,
        "score_type": score_type,
        "uni_types": uni_types,
        "departments": departments,
        "geo_flags": geo_flags,
    }


def _build_recommendation_context(intent: dict, rec_service: "RecommendationService") -> str:
    """Intent → recommendation servisi → kısa context string."""
    try:
        st_enum = ScoreType(intent["score_type"]) if isinstance(intent["score_type"], str) else intent["score_type"]
    except ValueError:
        st_enum = ScoreType.SAY

    profile = StudentProfile(
        score_type=st_enum,
        score=intent.get("score"),
        rank=intent.get("rank"),
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

        # Model tercihi (varsa) — multi-router'da kullanılır
        model_pref = getattr(query, "model_preference", None) or "gemini"

        text = ""
        try:
            # MultiLLMRouter model_preference parametresi alır; tek-model provider'lar yoksayar
            kwargs = {"context": context, "history": history_dicts if history_dicts else None}
            if hasattr(self._llm, "_providers"):  # MultiLLMRouter
                kwargs["model_preference"] = model_pref
            text = self._llm.generate(query.text, **kwargs)
        except Exception as e:  # noqa: BLE001
            logger.warning("llm_failed", error=str(e)[:200])
            text = f"⚠️ Şu an cevap üretemedim: {str(e)[:120]}"

        total_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "ask_completed",
            query_len=len(query.text),
            docs=len(docs),
            has_recommendation=bool(rec_context),
            total_ms=total_ms,
        )

        return Answer(
            query=query.text,
            text=text,
            docs=docs,
            total_latency_ms=total_ms,
        )
