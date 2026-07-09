"""ChromaDB vector store — UniSense."""
from __future__ import annotations

import os
from functools import lru_cache

import chromadb

from unisense.core.config import get_settings
from unisense.core.logging import get_logger
from unisense.domain.models import Chunk

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _get_embedding_model():
    # Lazy import: sentence_transformers (torch) ağır — modül import edilirken
    # değil, ilk kullanımda yüklensin (test/startup hızı)
    from sentence_transformers import SentenceTransformer

    settings = get_settings()
    logger.info("loading_embedding_model", model=settings.embedding_model)
    return SentenceTransformer(settings.embedding_model)


class ChromaVectorStore:
    """ChromaDB persistent client."""

    def __init__(self) -> None:
        settings = get_settings()
        persist_dir = os.path.abspath(settings.chroma_persist_dir)
        os.makedirs(persist_dir, exist_ok=True)
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=settings.chroma_collection,
            metadata={"hnsw:space": "l2"},
        )
        logger.info(
            "chroma_initialized",
            collection=settings.chroma_collection,
            count=self._collection.count(),
        )

    @property
    def collection(self):  # type: ignore[no-untyped-def]
        return self._collection

    def count(self) -> int:
        return self._collection.count()

    def warmup(self) -> None:
        """Cold start sırasında embedding modeli + ChromaDB index'i ısıtır.

        Bu fonksiyon ilk gerçek kullanıcı sorgusundan önce çağrılırsa
        SentenceTransformer model dosyaları diske okunur, CUDA/CPU init
        yapılır ve HNSW index ilk query ile yüklenir. Sonuç: p50 latency
        ~10sn → ~4sn.
        """
        try:
            model = _get_embedding_model()
            _ = model.encode(["ısınma sorgusu"], convert_to_numpy=True)
            # ChromaDB index'i de ısıt
            _ = self._collection.query(query_texts=["ısınma"], n_results=1)
            logger.info("warmup_done", chunks=self._collection.count())
        except Exception as e:
            logger.warning("warmup_failed", error=str(e))

    def search(
        self,
        query: str,
        top_k: int = 6,
        filters: dict | None = None,
    ) -> list[Chunk]:
        model = _get_embedding_model()
        embedding = model.encode([query], convert_to_numpy=True).tolist()

        result = self._collection.query(
            query_embeddings=embedding,
            n_results=top_k,
            where=filters,
            include=["documents", "metadatas", "distances"],
        )

        chunks: list[Chunk] = []
        if not result["ids"] or not result["ids"][0]:
            return chunks

        for i, chunk_id in enumerate(result["ids"][0]):
            meta = result["metadatas"][0][i] or {}
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    content=result["documents"][0][i] or "",
                    chunk_type=meta.get("chunk_type", "general"),
                    university_code=meta.get("university_code", ""),
                    department_code=meta.get("department_code", ""),
                    score_type=meta.get("score_type", ""),
                    year=meta.get("year"),
                    city=meta.get("city", ""),
                    heading=meta.get("heading", ""),
                    source=meta.get("source", "Unknown"),
                    source_url=meta.get("source_url", ""),
                    language=meta.get("language", "tr"),
                    distance=result["distances"][0][i] if result.get("distances") else None,
                )
            )
        return chunks
