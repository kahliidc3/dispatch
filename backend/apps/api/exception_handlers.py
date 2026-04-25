from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from libs.core.errors import InternalServerError, ValidationError, dispatchError
from libs.core.logging import get_logger, get_request_id

logger = get_logger("api.exceptions")


def _request_id_from_request(request: Request) -> str | None:
    return getattr(request.state, "request_id", None) or get_request_id()


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(dispatchError)
    async def dispatch_error_handler(request: Request, exc: dispatchError) -> JSONResponse:
        payload = exc.to_payload(_request_id_from_request(request))
        return JSONResponse(status_code=exc.status_code, content=payload)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        dispatch_exc = ValidationError(details={"errors": exc.errors()})
        return JSONResponse(
            status_code=dispatch_exc.status_code,
            content=dispatch_exc.to_payload(_request_id_from_request(request)),
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("api.unhandled_exception", error=str(exc))
        dispatch_exc = InternalServerError()
        return JSONResponse(
            status_code=dispatch_exc.status_code,
            content=dispatch_exc.to_payload(_request_id_from_request(request)),
        )
