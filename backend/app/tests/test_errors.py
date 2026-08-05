import asyncio

from fastapi import Request
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.api.v1 import health
from app.core.errors import APIError
from app.core.errors import database_error_handler


def test_api_error_carries_stable_contract_fields() -> None:
    error = APIError(status_code=422, code="invalid_input", message="Invalid input.")

    assert error.status_code == 422
    assert error.code == "invalid_input"
    assert error.message == "Invalid input."
    assert str(error) == "Invalid input."


def test_database_error_handler_returns_service_unavailable() -> None:
    scope = {
        "type": "http",
        "method": "POST",
        "scheme": "http",
        "server": ("testserver", 80),
        "path": "/register",
        "root_path": "",
        "query_string": b"",
        "headers": [],
    }
    request = Request(scope)
    error = OperationalError("select 1", {}, Exception("connection refused"))

    response = asyncio.run(database_error_handler(request, error))

    assert response.status_code == 503
    assert b"database_unavailable" in response.body
    assert b"Database unavailable" in response.body


def test_readiness_check_returns_503_when_database_is_unavailable(monkeypatch) -> None:
    def broken_session_local() -> None:
        raise SQLAlchemyError("database unavailable")

    monkeypatch.setattr(health, "SessionLocal", broken_session_local)

    response = health.readiness_check()

    assert response.status_code == 503
    assert b"unavailable" in response.body


def test_readiness_check_returns_200_when_database_is_available(monkeypatch) -> None:
    class WorkingSession:
        def __enter__(self) -> "WorkingSession":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def execute(self, *args: object, **kwargs: object) -> None:
            return None

    monkeypatch.setattr(health, "SessionLocal", WorkingSession)

    response = health.readiness_check()

    assert response.status_code == 200
    assert b"ready" in response.body
