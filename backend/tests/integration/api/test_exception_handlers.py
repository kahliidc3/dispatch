import pytest
from fastapi import FastAPI
from fastapi.routing import APIRouter
from httpx import ASGITransport, AsyncClient

from apps.api.exception_handlers import register_exception_handlers
from apps.api.middleware import RequestContextMiddleware
from libs.core.errors import (
    AuthenticationError,
    CircuitOpenError,
    ConflictError,
    ExternalServiceError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitedError,
    ValidationError,
)


@pytest.fixture
def exception_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(app)

    router = APIRouter()

    @router.get("/raise/{kind}")
    async def raise_error(kind: str) -> None:
        mapping = {
            "validation": ValidationError("validation failed"),
            "auth": AuthenticationError("auth failed"),
            "forbidden": PermissionDeniedError("forbidden"),
            "notfound": NotFoundError("missing"),
            "conflict": ConflictError("conflict"),
            "rate": RateLimitedError("slow down"),
            "external": ExternalServiceError("downstream failed"),
            "circuit": CircuitOpenError("circuit open"),
        }
        raise mapping[kind]

    @router.get("/validate")
    async def validate_endpoint(value: int) -> dict[str, int]:
        return {"value": value}

    @router.get("/explode")
    async def explode() -> None:
        raise RuntimeError("boom")

    app.include_router(router)
    return app


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("kind", "status", "code"),
    [
        ("validation", 422, "validation_error"),
        ("auth", 401, "authentication_error"),
        ("forbidden", 403, "permission_denied"),
        ("notfound", 404, "not_found"),
        ("conflict", 409, "conflict"),
        ("rate", 429, "rate_limited"),
        ("external", 502, "external_service_error"),
        ("circuit", 503, "circuit_open"),
    ],
)
async def test_typed_errors_map_to_http(
    exception_test_app: FastAPI,
    kind: str,
    status: int,
    code: str,
) -> None:
    transport = ASGITransport(app=exception_test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(f"/raise/{kind}", headers={"x-request-id": "req-abc"})

    assert response.status_code == status
    payload = response.json()
    assert payload["error"]["code"] == code
    assert payload["error"]["request_id"] == "req-abc"
    assert response.headers["x-request-id"] == "req-abc"


@pytest.mark.asyncio
async def test_fastapi_validation_error_shape(exception_test_app: FastAPI) -> None:
    transport = ASGITransport(app=exception_test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/validate", params={"value": "oops"})

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == "validation_error"
    assert "errors" in payload["error"]["details"]


@pytest.mark.asyncio
async def test_unhandled_error_maps_to_internal_server_error(exception_test_app: FastAPI) -> None:
    transport = ASGITransport(app=exception_test_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/explode")

    assert response.status_code == 500
    payload = response.json()
    assert payload["error"]["code"] == "internal_server_error"
