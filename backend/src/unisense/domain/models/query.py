"""Sorgu ve cevap modelleri."""
from __future__ import annotations

from pydantic import BaseModel, Field

from unisense.domain.enums import QueryIntent, ScoreType
from unisense.domain.models.chunk import Chunk
from unisense.domain.models.ranking import RankingRange


class ChatTurn(BaseModel):
    """Sohbet geçmişindeki tek tur."""
    role: str  # "user" | "bot"
    text: str


class Query(BaseModel):
    """Kullanıcı sorgu modeli."""
    text: str = Field(..., min_length=1, max_length=500)
    intent_hint: QueryIntent | None = None
    score_type: ScoreType | None = None
    user_rank: int | None = None
    user_score: float | None = None
    top_k: int = Field(default=12, ge=1, le=30)
    history: list[ChatTurn] = Field(default_factory=list)
    # Hangi LLM kullanılsın: "gemini" (default) | "unisense-local"
    model_preference: str = "gemini"


class Answer(BaseModel):
    """Cevap — text + ilgili veri."""
    query: str
    text: str = ""                              # LLM'in ürettiği cevap
    docs: list[Chunk] = Field(default_factory=list)  # RAG context kaynakları
    rankings: list[RankingRange] = Field(default_factory=list)  # ilgili sıralamalar
    intent: QueryIntent = QueryIntent.GENERAL
    total_latency_ms: int | None = None
