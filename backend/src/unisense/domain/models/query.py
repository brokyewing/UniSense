"""Sorgu ve cevap modelleri."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from unisense.domain.enums import QueryIntent, ScoreType
from unisense.domain.models.chunk import Chunk
from unisense.domain.models.ranking import RankingRange


class CoachAction(BaseModel):
    """Gemini / AI koç tarafından üretilen doğrulanmış sistem aksiyonu."""

    type: Literal[
        "set_daily_goal",
        "create_study_plan",
        "log_questions",
        "add_task",
        "mark_topic_done",
        "add_preference",
        "add_deneme",
        "complete_task",
        "add_note",
        "log_study_time",
        "update_profile",
        "remove_preference",
        "reorder_preferences",
        "delete_task",
        "reschedule_task",
        "complete_note",
        "delete_note",
        "unmark_topic_done",
        "open_compare",
    ]
    label: str = Field(..., max_length=160)
    auto_apply: bool = True
    payload: dict = Field(default_factory=dict)


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
    actions: list[CoachAction] = Field(default_factory=list)
