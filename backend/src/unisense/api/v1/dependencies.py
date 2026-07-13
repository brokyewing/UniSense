"""FastAPI Depends helpers."""
from __future__ import annotations

from unisense.application.services import (
    AskService,
    CompareService,
    CompassService,
    RecommendationService,
)
from unisense.core.di import (
    get_ask_service as _di_ask,
    get_compare_service as _di_compare,
    get_compass_service as _di_compass,
    get_recommendation_service as _di_rec,
)


def ask_service_dep() -> AskService:
    return _di_ask()


def recommendation_service_dep() -> RecommendationService:
    return _di_rec()


def compass_service_dep() -> CompassService:
    return _di_compass()


def compare_service_dep() -> CompareService:
    return _di_compare()


def kpss_service_dep():
    from unisense.core.di import get_kpss_service
    return get_kpss_service()


def dgs_service_dep():
    from unisense.core.di import get_dgs_service
    return get_dgs_service()


def guide_service_dep():
    from unisense.core.di import get_guide_service
    return get_guide_service()


def news_service_dep():
    from unisense.core.di import get_news_service
    return get_news_service()


def lgs_service_dep():
    from unisense.core.di import get_lgs_service
    return get_lgs_service()


def tus_service_dep():
    from unisense.core.di import get_tus_service
    return get_tus_service()
