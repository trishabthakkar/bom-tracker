from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.auth import router as auth_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.errors import APIError, api_error_handler
from app.core.logging import configure_logging
from app.middleware.auth import JWTAuthenticationMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="API for BOM change intelligence workflows.",
    )

    app.add_exception_handler(APIError, api_error_handler)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(JWTAuthenticationMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth_router)
    app.include_router(api_router, prefix="/api/v1")
    return app


app = create_app()
