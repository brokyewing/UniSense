"""Hibrit Retrieval service — keyword + vector birlikte."""
from __future__ import annotations

import re
import unicodedata

import chromadb

from unisense.application.interfaces.vector_store import VectorStore
from unisense.core.config import get_settings
from unisense.core.logging import get_logger
from unisense.domain.models import Chunk, Query

logger = get_logger(__name__)


def _strip_accents(s: str) -> str:
    """ı→i, İ→I, vb. ASCII normalize."""
    s = s.replace("İ", "I").replace("ı", "i")
    s = s.replace("Ş", "S").replace("ş", "s")
    s = s.replace("Ğ", "G").replace("ğ", "g")
    s = s.replace("Ü", "U").replace("ü", "u")
    s = s.replace("Ö", "O").replace("ö", "o")
    s = s.replace("Ç", "C").replace("ç", "c")
    return s


def _tr_lower(s: str) -> str:
    """Türkçe-doğru lower: I→ı (dotless), İ→i (dotted)."""
    return s.replace("I", "ı").replace("İ", "i").lower()


def _tr_upper(s: str) -> str:
    """Türkçe-doğru upper: i→İ (dotted), ı→I (dotless)."""
    return s.replace("i", "İ").replace("ı", "I").upper()


def _tr_title(s: str) -> str:
    """Türkçe-safe title case."""
    out = []
    for w in s.split():
        if not w:
            continue
        first = _tr_upper(w[0])
        rest = w[1:]
        # rest'in upper karakterlerini lower'a çevir
        rest = rest.replace("İ", "i").replace("I", "ı")
        rest = rest.replace("Ş", "ş").replace("Ğ", "ğ")
        rest = rest.replace("Ü", "ü").replace("Ö", "ö").replace("Ç", "ç")
        out.append(first + rest.lower().replace("ı", "ı"))  # corner cases
    return " ".join(out)


def _detect_university_keywords(text: str) -> list[str]:
    """Sorguda 'X Üniversitesi' / 'X Teknik' tespit et — TÜRKÇE karakter koru.

    Sonuçlar TÜM ÇEŞİTLERİYLE döndürülür (Türkçe + ASCII normalize'lı + UPPER):
    böylece ChromaDB $contains case-sensitive arama tutar.
    """
    keywords_raw: list[str] = []

    # "X Üniversitesi" / "X Teknik Üniversitesi" — TR character'lara izin ver
    text_lower = _tr_lower(text)  # Türkçe-doğru lower
    patterns = [
        # "iskenderun teknik üniversitesi" → "iskenderun teknik"
        r"([a-zçğıöşüâîû\s]{3,40})\s+üniversit",
        # "iskenderun teknik" tek başına da yakala
        r"([a-zçğıöşüâîû\s]{3,40})\s+teknik\b",
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, text_lower):
            kw = m.group(1).strip()
            # 'bu/tüm/her' gibi yaygın kelimelerle başlamasın
            for skip in ("bu ", "tüm ", "her ", "bir ", "gibi ", "olan ", "için ",
                         "hangi", "hakkında"):
                if kw.startswith(skip):
                    kw = kw[len(skip):].strip()
            if len(kw) >= 3:
                keywords_raw.append(kw)

    # Yaygın üniversite isimleri
    SHORT_NAMES = ["itü", "itu", "odtü", "odtu", "boğaziçi", "bogazici",
                   "yıldız teknik", "yildiz teknik", "marmara",
                   "hacettepe", "ankara", "istanbul", "ege", "selçuk", "iskenderun",
                   "karabük", "karabuk", "sabancı", "sabanci", "koç", "koc",
                   "bilkent", "trabzon", "kocaeli", "atılım", "atilim",
                   "yeditepe", "bahçeşehir", "bahcesehir", "gazi", "gebze",
                   "anadolu", "akdeniz", "çukurova", "cukurova", "uludağ", "uludag"]
    for n in SHORT_NAMES:
        if re.search(rf"\b{re.escape(n)}\b", text_lower):
            keywords_raw.append(n)

    # Her keyword için ÇEŞİTLERİ üret (TR + ASCII + UPPER + Title)
    out: list[str] = []
    seen = set()
    for kw in keywords_raw:
        ascii_kw = _strip_accents(kw)
        for variant in (
            kw,                          # iskenderun teknik
            _tr_upper(kw),               # İSKENDERUN TEKNİK (TÜRKÇE upper!)
            _tr_title(kw),               # İskenderun Teknik
            kw.upper(),                  # ISKENDERUN TEKNIK (Python default)
            kw.title(),                  # Iskenderun Teknik
            ascii_kw,                    # iskenderun teknik (ascii)
            ascii_kw.upper(),            # ISKENDERUN TEKNIK
            ascii_kw.title(),            # Iskenderun Teknik
        ):
            if variant and variant not in seen:
                seen.add(variant)
                out.append(variant)
    return out


class RetrievalService:
    """Hibrit retrieval: keyword filter + vector search."""

    def __init__(self, store: VectorStore) -> None:
        self._store = store

    def _keyword_search(self, query: str, limit: int = 6) -> list[Chunk]:
        """ChromaDB metadata + content içinde kelime ara."""
        try:
            settings = get_settings()
            client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            collection = client.get_collection(settings.chroma_collection)

            # Sorgudaki üniversite-tipi keyword'leri çıkar
            kws = _detect_university_keywords(query)
            if not kws:
                return []

            # Her keyword variant için $contains filter
            chunks: list[Chunk] = []
            seen_ids = set()
            for variant in kws:
                if len(chunks) >= limit:
                    break
                try:
                    result = collection.get(
                        where_document={"$contains": variant},
                        limit=limit,
                    )
                    for i, cid in enumerate(result["ids"]):
                        if cid in seen_ids:
                            continue
                        seen_ids.add(cid)
                        meta = result["metadatas"][i] or {}
                        chunks.append(Chunk(
                            chunk_id=cid,
                            content=result["documents"][i] or "",
                            heading=meta.get("heading", ""),
                            source=meta.get("source", "Unknown"),
                            source_url=meta.get("source_url", ""),
                            language=meta.get("language", "tr") or "tr",
                            university_code=meta.get("university_code", ""),
                            department_code=meta.get("department_code", ""),
                            year=meta.get("year"),
                            city=meta.get("city", ""),
                            score_type=meta.get("score_type", ""),
                            chunk_type=meta.get("chunk_type", "general"),
                            distance=0.0,  # keyword match — exact
                        ))
                        if len(chunks) >= limit:
                            break
                except Exception:
                    continue
            return chunks[:limit]
        except Exception as e:  # noqa: BLE001
            logger.warning("keyword_search_failed", error=str(e)[:120])
            return []

    def retrieve(self, query: Query) -> list[Chunk]:
        # 1) Keyword search — exact match önce
        keyword_results = self._keyword_search(query.text, limit=query.top_k)

        # 2) Vector search — semantic
        vector_results = self._store.search(
            query=query.text,
            top_k=query.top_k,
            filters=None,
        )

        # 3) Birleştir — keyword sonuçları ÖNCE (mesafe=0), vector sonra
        seen_ids = {c.chunk_id for c in keyword_results}
        combined = list(keyword_results)
        for c in vector_results:
            if c.chunk_id not in seen_ids:
                combined.append(c)
                seen_ids.add(c.chunk_id)
            if len(combined) >= query.top_k * 2:
                break

        # En fazla top_k * 2 dön (LLM context limiti)
        return combined[: query.top_k * 2]

    def build_context(self, docs: list[Chunk]) -> str:
        if not docs:
            return ""
        parts = []
        for d in docs:
            header_bits = []
            if d.university_code:
                header_bits.append(f"Üni: {d.university_code}")
            if d.department_code:
                header_bits.append(f"Bölüm: {d.department_code}")
            if d.year:
                header_bits.append(f"Yıl: {d.year}")
            header = f"[{' | '.join(header_bits) or d.source}]"
            parts.append(f"{header}\n{d.content}")
        return "\n\n---\n\n".join(parts)
