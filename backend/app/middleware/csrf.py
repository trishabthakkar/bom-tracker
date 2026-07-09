from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.middleware.auth import AUTH_COOKIE_NAME

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
CSRF_EXEMPT_PATHS = {
    "/docs",
    "/openapi.json",
    "/redoc",
    "/register",
    "/login",
    "/api/v1/register",
    "/api/v1/login",
    "/api/v1/health",
}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if self._requires_csrf(request):
            cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
            header_token = request.headers.get(CSRF_HEADER_NAME)

            if not cookie_token or not header_token or cookie_token != header_token:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token missing or invalid."},
                )

        return await call_next(request)

    def _requires_csrf(self, request: Request) -> bool:
        path = request.url.path

        if request.method in SAFE_METHODS or path in CSRF_EXEMPT_PATHS:
            return False

        return AUTH_COOKIE_NAME in request.cookies
