"""Audit logging."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path

from unisense.core.config import get_settings
from unisense.core.logging import get_logger

logger = get_logger(__name__)


def _hash_query(query: str) -> str:
    return sha256(query.encode("utf-8")).hexdigest()[:16]


def audit(event: str, *, ip=None, user_agent=None, query=None,
          api_key_prefix=None, extra=None) -> None:
    settings = get_settings()
    record = {
        "ts": datetime.now(tz=timezone.utc).isoformat(),
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
        record.update(extra)

    path = Path(settings.audit_log_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:  # noqa: BLE001
        logger.error("audit_write_failed", error=str(e), path=str(path))
    # structlog'a "event" key'i çakışmaması için rename
    record_safe = {k if k != "event" else "audit_event": v for k, v in record.items()}
    logger.info("audit", **record_safe)
