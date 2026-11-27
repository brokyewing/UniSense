"""Audit logging."""
from __future__ import annotations

import json
import logging
import threading
from datetime import UTC, datetime
from hashlib import sha256
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from unisense.core.config import get_settings
from unisense.core.logging import get_logger

logger = get_logger(__name__)

_HANDLER_LOCK = threading.Lock()
_HANDLERS: dict[str, TimedRotatingFileHandler] = {}


def _get_audit_handler(path: Path) -> TimedRotatingFileHandler:
    key = str(path.resolve())
    with _HANDLER_LOCK:
        handler = _HANDLERS.get(key)
        if handler is None:
            path.parent.mkdir(parents=True, exist_ok=True)
            handler = TimedRotatingFileHandler(
                str(path),
                when="midnight",
                interval=1,
                backupCount=30,
                encoding="utf-8",
                utc=True,
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            _HANDLERS[key] = handler
        return handler


def _hash_query(query: str) -> str:
    return sha256(query.encode("utf-8")).hexdigest()[:16]


def audit(event: str, *, ip=None, user_agent=None, query=None,
          api_key_prefix=None, extra=None) -> None:
    settings = get_settings()
    record = {
        "ts": datetime.now(tz=UTC).isoformat(),
        "event": event,
        "env": settings.app_env,
    }
    if ip:
        record["ip"] = ip
    if user_agent:
        record["ua"] = user_agent[:200]
    if query:
        record["query_hash"] = _hash_query(query)
        record["query_len"] = len(query)
    if api_key_prefix:
        record["api_key_prefix"] = api_key_prefix
    if extra:
        record.update({k: v for k, v in extra.items() if v is not None})

    path = Path(settings.audit_log_path)
    try:
        handler = _get_audit_handler(path)
        line = json.dumps(record, ensure_ascii=False)
        with _HANDLER_LOCK:
            handler.emit(
                logging.LogRecord("unisense.audit", logging.INFO, "", 0, line, (), None)
            )
    except Exception as e:
        logger.error("audit_write_failed", error=str(e), path=str(path))
    # structlog'a "event" key'i çakışmaması için rename
    record_safe = {k if k != "event" else "audit_event": v for k, v in record.items()}
    logger.info("audit", **record_safe)
