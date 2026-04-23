from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from libs.core.config import get_settings
from libs.core.db.session import dispose_db, init_db
from libs.core.logging import configure_logging, get_logger

logger = get_logger("api.lifespan")


@asynccontextmanager
async def app_lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(service_name=settings.service_name, log_level=settings.log_level)
    await init_db()
    logger.info("api.startup.complete")
    try:
        yield
    finally:
        await dispose_db()
        logger.info("api.shutdown.complete")
