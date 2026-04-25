import pytest

from libs.core.errors import (
    AuthenticationError,
    CircuitOpenError,
    ConflictError,
    ExternalServiceError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitedError,
    ValidationError,
    dispatchError,
)


@pytest.mark.parametrize(
    ("error_type", "status_code", "code"),
    [
        (ValidationError, 422, "validation_error"),
        (AuthenticationError, 401, "authentication_error"),
        (PermissionDeniedError, 403, "permission_denied"),
        (NotFoundError, 404, "not_found"),
        (ConflictError, 409, "conflict"),
        (RateLimitedError, 429, "rate_limited"),
        (ExternalServiceError, 502, "external_service_error"),
        (CircuitOpenError, 503, "circuit_open"),
        (InternalServerError, 500, "internal_server_error"),
    ],
)
def test_error_subclass_status_and_code(
    error_type: type[dispatchError],
    status_code: int,
    code: str,
) -> None:
    error = error_type("boom")

    assert error.status_code == status_code
    assert error.code == code


def test_error_payload_shape() -> None:
    error = ValidationError("bad input", details={"field": "email"})

    payload = error.to_payload(request_id="req-123")

    assert payload == {
        "error": {
            "code": "validation_error",
            "message": "bad input",
            "details": {"field": "email"},
            "request_id": "req-123",
        }
    }
