"""Ask service — RAG sorgu orkestrasyonu + sıra/puan intent routing.

Intent analizi ve context inşa: intent_router modülüne taşındı.
"""
from __future__ import annotations

import hashlib
import re
import time
from typing import TYPE_CHECKING

from cachetools import TTLCache

from unisense.application.interfaces.llm_provider import LLMProvider
from unisense.application.services.coach_action_service import (
    build_coach_action_context,
    detect_preference_add_intent,
    extract_coach_actions,
    fallback_coach_reply,
    has_user_action_intent,
    merge_coach_actions,
    parse_llm_actions_and_strip,
)
from unisense.application.services.intent_router import (
    DGS_RE,
    GENERIC_PLACEMENT_RE,
    KPSS_AGG_RE,
    KPSS_RE,
    SELF_SCORE_RE,
    build_dgs_context,
    build_kpss_context,
    build_profile_context,
    build_recommendation_context,
    extract_intent,
    rankings_year,
    routing_text,
)
from unisense.application.services.retrieval_service import RetrievalService
from unisense.application.services.trend_service import has_history, trend_summary
from unisense.core.logging import get_logger
from unisense.domain.models import Answer, Query

if TYPE_CHECKING:
    from unisense.application.services.recommendation_service import RecommendationService

logger = get_logger(__name__)

# Cevap önbelleği — aynı sorgu (+ history + model) için Gemini'yi tekrar çağırmaktan kaçın.
# maxsize=512 ~5 MB civarı; ttl=3600 (1 saat) — güncel veri sınırı.
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


# === Gemini öncesi PII maskeleme (TCKN / e-posta / TR telefon) ===
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_TCKN_RE = re.compile(r"\b[1-9]\d{10}\b")
_TR_PHONE_RE = re.compile(r"(?:\+?90\s*|0)?5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}\b")


def _scrub_pii(text: str) -> str:
    if not text:
        return text
    cleaned = _EMAIL_RE.sub("[E-POSTA MASKELENDİ]", text)
    cleaned = _TCKN_RE.sub("[TCKN MASKELENDİ]", cleaned)
    cleaned = _TR_PHONE_RE.sub("[TELEFON MASKELENDİ]", cleaned)
    return cleaned


_EMPTY_CONTEXT_ANSWER = (
    "• UniSense YÖK Atlas ve ÖSYM indeksinde bu soruyla doğrudan eşleşen doğrulanmış kayıt bulunamadı.\n"
    "• Lütfen soruyu üniversite adı, bölüm adı, sınav türü (YKS/DGS/KPSS) veya puan türüyle biraz daha netleştir.\n"
    "• Resmî teyit için: https://yokatlas.yok.gov.tr ve https://www.osym.gov.tr"
)


# Trend / yıllar arası sorgu pattern'i (ask_service'e özgü)
_TREND_PATTERNS = [
    re.compile(r"\btrend"),
    re.compile(r"\b(y(ı|i)l|y(ı|i)llar)\s+(i(ç|c)inde|aras(ı|i))"),
    re.compile(r"\bge(ç|c)mi(ş|s)"),
    re.compile(r"\b(20\d\d)\s*[-–]\s*(20\d\d)"),  # "2020-2024"
    re.compile(r"y(ü|u)kseli|d(ü|u)(ş|s)(ü|u)"),  # "yükseliş/düşüş"
    re.compile(r"\bson\s+\d+\s+y(ı|i)l"),
]


class AskService:
    """RAG (Gemini + ChromaDB) + sıra/puan intent → Recommend hybrid."""

    def __init__(
        self,
        retrieval: RetrievalService,
        llm: LLMProvider,
        recommendation: RecommendationService | None = None,
    ) -> None:
        self._retrieval = retrieval
        self._llm = llm
        self._recommendation = recommendation

    def execute(self, query: Query, user_context: dict | None = None) -> Answer:
        start = time.perf_counter()
        uc = user_context or {}
        actions = extract_coach_actions(query.text, uc)
        pref_intent = detect_preference_add_intent(query.text)
        history_codes: list[str] = []
        if pref_intent and query.history:
            for turn in query.history[-4:]:
                history_codes.extend(re.findall(r"\b(\d{9})\b", turn.text or ""))
            history_codes = list(dict.fromkeys(history_codes))
        coach_context = build_coach_action_context(
            actions,
            uc,
            pref_intent=pref_intent,
            history_codes=history_codes,
        )

        # 0. Cache check — aksiyon veya tercih ekleme içeren istekler her seferinde taze çalışır
        model_pref = getattr(query, "model_preference", None) or "gemini"
        cache_key = _make_cache_key(query, model_pref, user_context)
        cached_text = None if (actions or pref_intent) else _response_cache.get(cache_key)
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
        # ROUTING metni bağlamsaldır: kısa takip mesajları ("tüm illerde bak")
        # önceki soruyla birleşir (bkz. routing_text) → chat bağlamı korunur.
        rt = routing_text(query)
        sinav_context = ""
        uc_track = (user_context or {}).get("exam_track")
        try:
            if KPSS_RE.search(rt):
                sinav_context = build_kpss_context(rt, user_context)
                logger.info("kpss_intent_routed")
            elif DGS_RE.search(rt):
                sinav_context = build_dgs_context(rt, user_context)
                logger.info("dgs_intent_routed")
            elif uc_track == "KPSS" and (
                GENERIC_PLACEMENT_RE.search(rt)
                or KPSS_AGG_RE.search(rt)
            ):
                # Sınav adı yazılmamış ama kullanıcının yolu KPSS —
                # "toplam kaç kontenjan" gibi istatistik soruları da dahil
                sinav_context = build_kpss_context(rt, user_context)
                logger.info("kpss_intent_routed", via="exam_track")
            elif uc_track == "DGS" and GENERIC_PLACEMENT_RE.search(rt):
                sinav_context = build_dgs_context(rt, user_context)
                logger.info("dgs_intent_routed", via="exam_track")
        except Exception as e:
            logger.warning("sinav_context_failed", error=str(e)[:200])

        # 1. Intent kontrolü — sıra/puan tabanlı sorgu mu? (bağlamsal metinle)
        intent = extract_intent(rt) if not sinav_context else None

        # 1b. PROFİL YKS PUANI — kullanıcı mesajda puan yazmadıysa profildekini kullan
        # ("puanıma göre X kazanabilir miyim"). Mesajdaki açık puan HER ZAMAN öncelikli.
        uc = user_context or {}
        yks_puan = uc.get("yks_puan")
        if yks_puan and not sinav_context:
            if intent is not None and intent.get("score") is None and intent.get("rank") is None:
                # Bölüm/üni sorusu var, puan yok → profildeki puanı KIYAS için kat
                intent["user_score"] = yks_puan
                intent["user_score_type"] = uc.get("yks_turu")
                intent["user_rank"] = uc.get("yks_sira")
            elif intent is None and SELF_SCORE_RE.search(rt):
                # "puanıma göre nereye girerim" — mesajda bölüm de yok → profilden öneri
                intent = {
                    "rank": uc.get("yks_sira"), "score": yks_puan,
                    "score_type": uc.get("yks_turu") or "SAY",
                    "uni_types": [], "departments": [], "cities": [], "universities": [],
                    "geo_flags": [], "is_count": False, "is_net": False,
                    "obp_katki": None, "list_n": None,
                }

        rec_context = ""
        if intent and self._recommendation is not None:
            try:
                rec_context = build_recommendation_context(intent, self._recommendation)
                logger.info(
                    "intent_routed",
                    rank=intent.get("rank"),
                    score=intent.get("score"),
                    score_type=intent.get("score_type"),
                    uni_types=intent.get("uni_types"),
                    departments=intent.get("departments"),
                )
            except Exception as e:
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
                    f"Şu anda {rankings_year()} verisi var. Geçmiş yıl arşivi "
                    f"({rankings_year() - 5}-{rankings_year() - 1}) hazırlanıyor — "
                    "trend sorularına şu an cevap için Wikipedia/üni sayfalarındaki sözel "
                    "bilgilerle yetenin."
                )

        # 3. Context'i birleştir — PROFİL (en üstte), sınav, recommendation, trend, RAG
        parts = []
        profile_context = build_profile_context(uc)
        if profile_context:
            parts.append(profile_context)
        if coach_context:
            parts.append(coach_context)
        if sinav_context:
            parts.append(sinav_context)
        if rec_context:
            parts.append(rec_context)
        if trend_context:
            parts.append(trend_context)
        if rag_context:
            parts.append("=== EK RAG KAYNAKLARI ===\n" + rag_context)
        context = "\n\n".join(parts) if parts else rag_context

        # 4. Boş retrieval koruması + PII maskelemesi sonrası LLM cevabı
        if not sinav_context and not rec_context and not rag_context and not coach_context:
            total_ms = int((time.perf_counter() - start) * 1000)
            logger.info("ask_empty_context", query_len=len(query.text), total_ms=total_ms)
            return Answer(
                query=query.text,
                text=_EMPTY_CONTEXT_ANSWER,
                docs=[],
                total_latency_ms=total_ms,
            )

        history_dicts = []
        if query.history:
            for t in query.history:
                history_dicts.append({"role": t.role, "text": _scrub_pii(t.text)})

        scrubbed_query = _scrub_pii(query.text)
        text = ""
        llm_ok = False
        try:
            raw_text = self._llm.generate(
                scrubbed_query,
                context=context,
                history=history_dicts if history_dicts else None,
            )
            default_sinav = str(uc.get("exam_track") or "YKS").upper()
            text, llm_actions = parse_llm_actions_and_strip(raw_text, default_sinav=default_sinav)
            if actions or pref_intent or has_user_action_intent(query.text):
                actions = merge_coach_actions(actions, llm_actions)
            elif llm_actions:
                logger.warning("unsolicited_llm_actions_dropped", count=len(llm_actions))
            llm_ok = True
        except Exception as e:
            # Ham exception (model adı/kota/kaynak yolu vb.) kullanıcı balonuna SIZMASIN
            logger.warning("llm_failed", error=str(e)[:200])
            text = fallback_coach_reply(actions) if actions else "⚠️ Şu an cevap üretemedim, lütfen birazdan tekrar dene."

        # Cevabı önbelleğe yaz (aksiyon veya tercih ekleme niyeti yoksa ve başarılı LLM cevabıysa)
        if llm_ok and text and not actions and not pref_intent:
            _response_cache[cache_key] = text

        total_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "ask_completed",
            query_len=len(query.text),
            docs=len(docs),
            has_recommendation=bool(rec_context),
            actions=len(actions),
            total_ms=total_ms,
            cache_size=len(_response_cache),
        )

        return Answer(
            query=query.text,
            text=text,
            docs=docs,
            total_latency_ms=total_ms,
            actions=actions,
        )