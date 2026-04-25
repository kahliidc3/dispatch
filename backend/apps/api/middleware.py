from __future__ import annotations

from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from libs.core.logging import bind_request_context, clear_request_context, get_logger

logger = get_logger("api.request")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Injects and propagates request/trace identifiers for logs and responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid4())
        trace_id = request.headers.get("x-trace-id") or request_id

        request.state.request_id = request_id
        request.state.trace_id = trace_id
        bind_request_context(request_id=request_id, trace_id=trace_id)

        try:
            response = await call_next(request)
        finally:
            logger.info("api.request.completed", path=request.url.path, method=request.method)
            clear_request_context()

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        return response
