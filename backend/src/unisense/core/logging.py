"""Yapılandırılmış logging."""
from __future__ import annotations

import io
import logging
import sys

import structlog

from unisense.core.config import get_settings


def _ensure_utf8_stdout() -> None:
    """Windows console UTF-8 değilse zorla UTF-8 yap (Türkçe karakter koruması)."""
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        else:
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True
            )
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def configure_logging() -> None:
    _ensure_utf8_stdout()

    settings = get_settings()
    level = getattr(logging, settings.app_log_level, logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    if settings.is_production:
        processors.append(structlog.processors.JSONRenderer(ensure_ascii=False))
    else:
        # ConsoleRenderer renkler kapalı (Windows console encoding güvenliği için)
        processors.append(structlog.dev.ConsoleRenderer(colors=False))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
