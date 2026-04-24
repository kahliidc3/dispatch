from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from pydantic import ValidationError as PydanticValidationError

from apps.webhook.handlers import handle_sns_envelope
from apps.webhook.schemas import SnsEnvelope
from apps.webhook.sns_verify import SnsVerificationError
from libs.core.errors import ValidationError
from libs.core.logging import get_logger

logger = get_logger("webhook.main")


@asynccontextmanager
async def webhook_lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(title="dispatch-webhook", lifespan=webhook_lifespan)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sns")
async def receive_sns(request: Request) -> dict[str, object]:
    try:
        raw_payload = await request.json()
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request body must be JSON",
        ) from exc

    try:
        envelope = SnsEnvelope.model_validate(raw_payload)
    except PydanticValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SNS envelope validation failed",
        ) from exc

    try:
        result = handle_sns_envelope(envelope=envelope)
    except SnsVerificationError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message
        ) from exc
    except Exception as exc:
        logger.exception("webhook.enqueue_failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to enqueue SNS event",
        ) from exc

    return {
        "status": result.status,
        "subscription_confirmed": result.subscription_confirmed,
    }
