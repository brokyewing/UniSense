"""Global exception handler."""
from __future__ import annotations

try:
    import sentry_sdk
except ImportError:  # pragma: no cover - opsiyonel izleme
    sentry_sdk = None  # type: ignore[assignment]
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from unisense.core.config import get_settings
from unisense.core.logging import get_logger
from unisense.domain.exceptions import DomainError

logger = get_logger(__name__)
_sentry_initialized_dsn: str | None = None


def install(app: FastAPI) -> None:
    global _sentry_initialized_dsn
    settings = get_settings()
    if sentry_sdk is not None and settings.glitchtip_dsn and settings.glitchtip_dsn != _sentry_initialized_dsn:
        sentry_sdk.init(
            dsn=settings.glitchtip_dsn,
            environment=settings.app_env,
            traces_sample_rate=0,
        )
        _sentry_initialized_dsn = settings.glitchtip_dsn
    @app.exception_handler(DomainError)
    async def _handle_domain_error(request: Request, exc: DomainError) -> JSONResponse:
        logger.warning(
            "domain_error",
            code=exc.code,
            status=exc.http_status,
            message=exc.message,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            },
        )

    @app.exception_handler(Exception)
    async def _handle_generic_error(request: Request, exc: Exception) -> JSONResponse:
        if sentry_sdk is not None and get_settings().glitchtip_dsn:
            sentry_sdk.capture_exception(exc)
        logger.exception(
            "unhandled_error",
            path=request.url.path,
            error=str(exc)[:200],
        )
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "Sunucu hatası"}},
        )
