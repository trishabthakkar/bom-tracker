from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError


class APIError(Exception):
    """Application-level exception with a stable JSON response contract."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


async def api_error_handler(request: Request, error: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content={
            "error": {
                "code": error.code,
                "message": error.message,
                "path": request.url.path,
            }
        },
    )


async def database_error_handler(
    request: Request,
    error: SQLAlchemyError,
) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "error": {
                "code": "database_unavailable",
                "message": "Database unavailable. Please start PostgreSQL and run migrations.",
                "path": request.url.path,
            }
        },
    )
