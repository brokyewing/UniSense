"""Global exception handler."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from unisense.core.logging import get_logger
from unisense.domain.exceptions import DomainError

logger = get_logger(__name__)


def install(app: FastAPI) -> None:
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
        logger.exception(
            "unhandled_error",
            path=request.url.path,
            error=str(exc)[:200],
        )
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message": "Sunucu hatası"}},
        )
