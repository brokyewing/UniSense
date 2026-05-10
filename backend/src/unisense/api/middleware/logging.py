"""Request log middleware."""
from __future__ import annotations

import time
import uuid

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware

from unisense.core.logging import get_logger

logger = get_logger(__name__)


class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())[:8]
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request_failed", method=request.method, path=request.url.path)
            raise

        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "request_done",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=duration_ms,
            request_id=request_id,
        )
        response.headers["x-request-id"] = request_id
        return response


def install(app: FastAPI) -> None:
    app.add_middleware(RequestLogMiddleware)
