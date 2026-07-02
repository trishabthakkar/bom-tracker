from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.security import decode_access_token

AUTH_COOKIE_NAME = "access_token"
PUBLIC_PATHS = {
    "/docs",
    "/openapi.json",
    "/redoc",
    "/register",
    "/login",
    "/logout",
    "/api/v1/register",
    "/api/v1/login",
    "/api/v1/logout",
    "/api/v1/health",
}
PROTECTED_PATHS = {"/me", "/api/v1/me"}
PROTECTED_PREFIXES = ("/api/v1",)


class JWTAuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request.state.user_id = None
        token = request.cookies.get(AUTH_COOKIE_NAME)

        authorization = request.headers.get("Authorization")
        if token is None and authorization and authorization.startswith("Bearer "):
            token = authorization.removeprefix("Bearer ").strip()

        if token:
            payload = decode_access_token(token)
            subject = payload.get("sub") if payload else None
            if isinstance(subject, str) and subject.isdigit():
                request.state.user_id = int(subject)

        if self._requires_authentication(request) and request.state.user_id is None:
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required."},
            )

        return await call_next(request)

    def _requires_authentication(self, request: Request) -> bool:
        path = request.url.path

        if request.method == "OPTIONS" or path in PUBLIC_PATHS:
            return False

        return path in PROTECTED_PATHS or any(
            path.startswith(prefix) for prefix in PROTECTED_PREFIXES
        )
