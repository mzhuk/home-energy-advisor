from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.errors import register_error_handlers
from app.core.logging import configure_logging, register_request_logging
from app.core.settings import Settings, get_settings
from app.db.schema import init_schema


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings: Settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        init_schema(resolved_settings.database_url)
        yield

    configure_logging()
    app = FastAPI(
        title="Home Energy Advisor API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(middleware_class=CorrelationIdMiddleware)
    app.add_middleware(
        middleware_class=CORSMiddleware,
        allow_origins=resolved_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.settings = resolved_settings
    register_error_handlers(app)
    register_request_logging(app)
    app.include_router(router=api_router, prefix=resolved_settings.api_prefix)
    return app


app: FastAPI = create_app()
