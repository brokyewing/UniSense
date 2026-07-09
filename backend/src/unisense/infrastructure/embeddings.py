"""Gemini embedding provider.

Lokal sentence-transformers/torch yerine Gemini embedding API kullanılır:
- Container RAM ~1.5GB → ~200MB (torch yok)
- Kalite: gemini-embedding-001 çok dilli MTEB'de MiniLM'den belirgin iyi
- Bedel: sorgu başına ~200-400ms API gecikmesi + Gemini'ye bağımlılık

Not: output_dimensionality < 3072 iken Gemini vektörleri normalize ETMEZ —
burada her zaman L2 normalize ediyoruz (cosine ≡ L2 karşılaştırması için şart).
"""
from __future__ import annotations

import random
import time

import numpy as np

from unisense.core.config import get_settings
from unisense.core.logging import get_logger
from unisense.domain.exceptions import UpstreamError

logger = get_logger(__name__)

# Gemini embedding input limiti ~2048 token; Türkçe'de ~4 karakter/token.
# Chunk içeriği bundan uzunsa embedding için kırpılır (dokümanın tamamı
# yine ChromaDB'de saklanır, sadece vektör kırpık metinden üretilir).
MAX_EMBED_CHARS = 7000
BATCH_LIMIT = 100  # batchEmbedContents üst sınırı

_key_idx = 0


def _next_key() -> str:
    global _key_idx
    keys = get_settings().gemini_keys_list
    if not keys:
        raise UpstreamError("Gemini key tanımlı değil (GEMINI_API_KEYS)")
    key = keys[_key_idx % len(keys)]
    _key_idx += 1
    return key


def _normalize(embs: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(embs, axis=1, keepdims=True) + 1e-9
    return (embs / norms).astype(np.float32)


def embed_texts(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    max_retries: int = 5,
) -> np.ndarray:
    """Metin listesini embed eder (normalize edilmiş float32 matris döner).

    Sağlayıcı EMBEDDING_PROVIDER config'inden seçilir:
      local  → ONNX MiniLM, task_type yok sayılır (model tek modlu)
      gemini → Gemini API; task_type: RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY /
               SEMANTIC_SIMILARITY. 429/5xx'te backoff + key rotasyonu.
    """
    settings = get_settings()
    if not texts:
        return np.zeros((0, settings.effective_embedding_dim), dtype=np.float32)

    if settings.embedding_provider == "local":
        from unisense.infrastructure.embeddings_local import embed_texts_local

        return embed_texts_local(texts)

    import google.generativeai as genai

    clipped = [(t or " ")[:MAX_EMBED_CHARS] for t in texts]

    all_embs: list[list[float]] = []
    for start in range(0, len(clipped), BATCH_LIMIT):
        batch = clipped[start:start + BATCH_LIMIT]
        last_err: Exception | None = None
        for attempt in range(max_retries):
            try:
                genai.configure(api_key=_next_key())
                result = genai.embed_content(
                    model=settings.gemini_embedding_model,
                    content=batch,
                    task_type=task_type,
                    output_dimensionality=settings.embedding_dim,
                )
                embs = result["embedding"]
                # Tek metinde düz vektör dönebilir
                if embs and isinstance(embs[0], (int, float)):
                    embs = [embs]
                all_embs.extend(embs)
                break
            except Exception as e:  # noqa: BLE001
                last_err = e
                msg = str(e)
                retriable = any(s in msg for s in ("429", "quota", "Quota", "503", "500", "deadline"))
                if not retriable or attempt == max_retries - 1:
                    logger.error("embed_failed", error=msg[:200], batch_start=start)
                    raise UpstreamError(f"Embedding hatası: {msg[:120]}") from e
                # Free tier kotası dakikalık pencerede sıfırlanır — backoff
                # penceresi aşacak kadar uzun olmalı (max 70sn)
                delay = min(2 ** attempt * 5 + random.uniform(0, 2), 70)
                logger.warning("embed_retry", attempt=attempt + 1, delay=round(delay, 1), error=msg[:120])
                time.sleep(delay)
        else:
            raise UpstreamError(f"Embedding hatası: {str(last_err)[:120]}") from last_err

    return _normalize(np.array(all_embs, dtype=np.float32))


def embed_query(text: str) -> np.ndarray:
    """Tek kullanıcı sorgusunu embed eder (1D normalize vektör)."""
    return embed_texts([text], task_type="RETRIEVAL_QUERY")[0]
