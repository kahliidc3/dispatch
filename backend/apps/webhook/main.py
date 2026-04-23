from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI


@asynccontextmanager
async def webhook_lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(title="dispatch-webhook", lifespan=webhook_lifespan)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
