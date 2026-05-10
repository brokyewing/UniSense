"""FastAPI app entrypoint.

Kullanım:
    uvicorn unisense.main:app --host 0.0.0.0 --port 8002 --reload
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from unisense.api.middleware import error_handler, logging as request_log, rate_limit
from unisense.api.v1.routes import router as v1_router
from unisense.core.config import get_settings
from unisense.core.logging import configure_logging, get_logger


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()
    logger = get_logger(__name__)

    app = FastAPI(
        title="UniSense API",
        version="0.1.0",
        description="UniSense — Türkiye üniversite tercih asistanı (RAG + sıralama veritabanı)",
        docs_url="/api/docs" if not settings.is_production else None,
        redoc_url="/api/redoc" if not settings.is_production else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
    )

    rate_limit.install(app)
    request_log.install(app)
    error_handler.install(app)

    app.include_router(v1_router)

    logger.info(
        "app_starting",
        env=settings.app_env,
        port=settings.app_port,
        cors_origins=settings.cors_origins_list,
    )
    return app


app = create_app()


def run() -> None:
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "unisense.main:app",
        host=settings.app_host,
        port=settings.app_port,
        log_level=settings.app_log_level.lower(),
        reload=not settings.is_production,
    )


if __name__ == "__main__":
    run()
