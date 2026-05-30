import asyncio
from collections import defaultdict, deque
from time import monotonic

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: object) -> None:
        super().__init__(app)
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path == "/health":
            return await call_next(request)

        settings = get_settings()
        client_host = request.client.host if request.client else "unknown"
        key = request.headers.get("X-API-Key") or client_host
        now = monotonic()
        window = 60.0
        limit = settings.rate_limit_per_minute

        async with self._lock:
            bucket = self._requests[key]
            while bucket and now - bucket[0] > window:
                bucket.popleft()
            if len(bucket) >= limit:
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded", "code": "RATE_LIMIT"},
                )
            bucket.append(now)

        return await call_next(request)
