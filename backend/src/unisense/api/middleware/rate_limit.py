"""Rate limiting."""
from __future__ import annotations

from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from unisense.core.config import get_settings


_settings = get_settings()
limiter = Limiter(key_func=get_remote_address)


def install(app: FastAPI) -> None:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


def ask_limit() -> str:
    return f"{_settings.rate_limit_ask}/minute"
