import json
import logging
import time
import uuid
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.database import async_session_factory
from app.models.db import AuditLog

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path == "/health":
            return await call_next(request)

        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)

        user_id = getattr(request.state, "user_id", None)
        request_id = getattr(request.state, "request_id", None)

        try:
            async with async_session_factory() as session:
                session.add(
                    AuditLog(
                        user_id=user_id,
                        request_id=request_id,
                        endpoint=request.url.path,
                        method=request.method,
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                    )
                )
                await session.commit()
        except Exception:
            logger.exception("Failed to write audit log")

        return response


def parse_filter_param(filter_param: str | None) -> list[dict[str, Any]]:
    if not filter_param:
        return []
    try:
        parsed = json.loads(filter_param)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict) and "filters" in parsed:
            return parsed["filters"]
    except json.JSONDecodeError:
        pass
    return []
