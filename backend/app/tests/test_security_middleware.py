import asyncio

from fastapi import Request
from starlette.responses import JSONResponse

from app.main import app
from app.middleware.auth import JWTAuthenticationMiddleware
from app.middleware.csrf import CSRFMiddleware
from app.middleware.rate_limit import InMemoryRateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware


def build_request(
    *,
    method: str,
    path: str,
    headers: list[tuple[bytes, bytes]] | None = None,
    client: tuple[str, int] = ("127.0.0.1", 12345),
) -> Request:
    return Request(
        {
            "type": "http",
            "method": method,
            "scheme": "http",
            "server": ("testserver", 80),
            "client": client,
            "path": path,
            "root_path": "",
            "query_string": b"",
            "headers": headers or [],
        }
    )


def test_csrf_policy_requires_token_for_cookie_authenticated_mutation() -> None:
    middleware = CSRFMiddleware(app=None)
    request = build_request(
        method="POST",
        path="/api/v1/uploads",
        headers=[(b"cookie", b"access_token=token")],
    )

    assert middleware._requires_csrf(request) is True


def test_csrf_policy_skips_public_login() -> None:
    middleware = CSRFMiddleware(app=None)
    request = build_request(method="POST", path="/login")

    assert middleware._requires_csrf(request) is False


def test_rate_limit_middleware_limits_auth_attempts() -> None:
    middleware = InMemoryRateLimitMiddleware(app=None)
    request = build_request(method="POST", path="/login")

    for _ in range(10):
        assert middleware._is_limited(request, limit=10) is False

    assert middleware._is_limited(request, limit=10) is True


def test_rate_limit_middleware_dispatches_after_auth_middleware() -> None:
    """FastAPI's add_middleware() prepends internally, so whichever
    middleware is registered LAST in app.main.create_app() dispatches
    FIRST on an incoming request. The rate limiter keys its bucket on
    request.state.user_id, which only JWTAuthenticationMiddleware sets, so
    auth must dispatch before rate limiting or every authenticated user
    silently falls back to sharing one IP-keyed bucket. This inspects the
    real, built middleware stack rather than re-deriving the order from
    source line numbers, since the ordering is otherwise invisible."""
    middleware_classes = [entry.cls for entry in app.user_middleware]

    rate_limit_index = middleware_classes.index(InMemoryRateLimitMiddleware)
    auth_index = middleware_classes.index(JWTAuthenticationMiddleware)

    assert auth_index < rate_limit_index


def test_security_headers_are_added() -> None:
    middleware = SecurityHeadersMiddleware(app=None)
    request = build_request(method="GET", path="/api/v1/health")

    async def call_next(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    response = asyncio.run(middleware.dispatch(request, call_next))

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
