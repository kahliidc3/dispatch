from fastapi import FastAPI

from apps.api.exception_handlers import register_exception_handlers
from apps.api.lifespan import app_lifespan
from apps.api.middleware import RequestContextMiddleware
from apps.api.routers import api_router

app = FastAPI(title="dispatch-api", lifespan=app_lifespan)
app.add_middleware(RequestContextMiddleware)
register_exception_handlers(app)
app.include_router(api_router)
