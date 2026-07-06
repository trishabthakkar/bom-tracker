import asyncio

from fastapi import Request
from sqlalchemy.exc import OperationalError

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
