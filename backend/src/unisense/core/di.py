"""Dependency Injection container."""
from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from unisense.application.interfaces.llm_provider import LLMProvider
    from unisense.application.interfaces.vector_store import VectorStore
    from unisense.application.services.ask_service import AskService
    from unisense.application.services.compass_service import CompassService
    from unisense.application.services.recommendation_service import RecommendationService
    from unisense.application.services.retrieval_service import RetrievalService


@lru_cache(maxsize=1)
def get_vector_store() -> VectorStore:
    from unisense.infrastructure.vector_store.chroma_store import ChromaVectorStore
    return ChromaVectorStore()


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """Multi-LLM router döner — Gemini + UniSenseLocal arasında geçiş yapabilir."""
    from unisense.infrastructure.llm.gemini import GeminiProvider
    from unisense.infrastructure.llm.qwen import QwenProvider
    from unisense.infrastructure.llm.multi_router import MultiLLMRouter
    return MultiLLMRouter(gemini=GeminiProvider(), qwen=QwenProvider())


@lru_cache(maxsize=1)
def get_retrieval_service() -> RetrievalService:
    from unisense.application.services.retrieval_service import RetrievalService
    return RetrievalService(store=get_vector_store())


@lru_cache(maxsize=1)
def get_ask_service() -> AskService:
    from unisense.application.services.ask_service import AskService
    return AskService(
        retrieval=get_retrieval_service(),
        llm=get_llm_provider(),
        recommendation=get_recommendation_service(),
    )


@lru_cache(maxsize=1)
def get_recommendation_service() -> RecommendationService:
    from unisense.application.services.recommendation_service import RecommendationService
    return RecommendationService(store=get_vector_store())


@lru_cache(maxsize=1)
def get_compass_service() -> CompassService:
    from unisense.application.services.compass_service import CompassService
    return CompassService()


def reset_di_cache() -> None:
    for fn in (
        get_vector_store, get_llm_provider, get_retrieval_service,
        get_ask_service, get_recommendation_service, get_compass_service,
    ):
        fn.cache_clear()
