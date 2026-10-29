"""Analytics veri modelleri."""
from __future__ import annotations

from pydantic import BaseModel


class AnalyticsEvent(BaseModel):
    """Kullanıcı davranış olayı."""
    event_type: str  # page_view, search, ask, compare, tercih_add, etc.
    page: str | None = None
    user_id: str | None = None
    metadata: dict | None = None
    timestamp: str | None = None


class AnalyticsSummary(BaseModel):
    """Analytics özet response."""
    total_events: int
    unique_users: int
    top_pages: list[dict]
    top_events: list[dict]
    daily_active: int
    not_: str | None = None