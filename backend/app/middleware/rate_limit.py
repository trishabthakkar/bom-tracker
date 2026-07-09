from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from time import monotonic

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings

AUTH_LIMITED_PATHS = {
    "/login",
    "/register",
    "/api/v1/login",
    "/api/v1/register",
}
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
WINDOW_SECONDS = 60


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        limit = self._limit_for_request(request)
        if limit is not None and self._is_limited(request, limit):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please wait and try again."},
            )

        return await call_next(request)

    def _limit_for_request(self, request: Request) -> int | None:
        if request.method == "OPTIONS":
            return None

        if request.url.path in AUTH_LIMITED_PATHS:
            return settings.auth_rate_limit_per_minute

        if request.method in MUTATING_METHODS and request.url.path.startswith("/api/v1"):
            return settings.mutation_rate_limit_per_minute

        return None

    def _is_limited(self, request: Request, limit: int) -> bool:
        now = monotonic()
        key = self._key_for_request(request)
        timestamps = self._requests[key]

        while timestamps and now - timestamps[0] > WINDOW_SECONDS:
            timestamps.popleft()

        if len(timestamps) >= limit:
            return True

        timestamps.append(now)
        return False

    def _key_for_request(self, request: Request) -> str:
        user_id = getattr(request.state, "user_id", None)
        subject = f"user:{user_id}" if user_id else f"ip:{request.client.host if request.client else 'unknown'}"
        return f"{subject}:{request.method}:{request.url.path}"
