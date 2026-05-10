"""FastAPI Depends helpers."""
from __future__ import annotations

from unisense.application.services import AskService, CompassService, RecommendationService
from unisense.core.di import (
    get_ask_service as _di_ask,
    get_compass_service as _di_compass,
    get_recommendation_service as _di_rec,
)


def ask_service_dep() -> AskService:
    return _di_ask()


def recommendation_service_dep() -> RecommendationService:
    return _di_rec()


def compass_service_dep() -> CompassService:
    return _di_compass()
