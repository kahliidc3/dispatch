from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class dispatchError(Exception):
    """Root error type for all domain and infrastructure exceptions."""

    code = "dispatch_error"
    status_code = 500
    default_message = "An unexpected dispatch error occurred"

    def __init__(
        self,
        message: str | None = None,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.details = dict(details or {})
        super().__init__(self.message)

    def to_payload(self, request_id: str | None) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "request_id": request_id,
            }
        }


class ValidationError(dispatchError):
    code = "validation_error"
    status_code = 422
    default_message = "The request payload failed validation"


class AuthenticationError(dispatchError):
    code = "authentication_error"
    status_code = 401
    default_message = "Authentication is required"


class PermissionDeniedError(dispatchError):
    code = "permission_denied"
    status_code = 403
    default_message = "You do not have permission to perform this action"


class NotFoundError(dispatchError):
    code = "not_found"
    status_code = 404
    default_message = "The requested resource was not found"


class ConflictError(dispatchError):
    code = "conflict"
    status_code = 409
    default_message = "The request conflicts with the current resource state"


class RateLimitedError(dispatchError):
    code = "rate_limited"
    status_code = 429
    default_message = "Too many requests"


class CircuitOpenError(dispatchError):
    code = "circuit_open"
    status_code = 503
    default_message = "The delivery circuit is currently open"


class ExternalServiceError(dispatchError):
    code = "external_service_error"
    status_code = 502
    default_message = "A downstream service request failed"


class InternalServerError(dispatchError):
    code = "internal_server_error"
    status_code = 500
    default_message = "An internal server error occurred"
