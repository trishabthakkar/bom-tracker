from app.core.errors import APIError


def test_api_error_carries_stable_contract_fields() -> None:
    error = APIError(status_code=422, code="invalid_input", message="Invalid input.")

    assert error.status_code == 422
    assert error.code == "invalid_input"
    assert error.message == "Invalid input."
    assert str(error) == "Invalid input."
