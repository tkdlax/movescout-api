import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request import AuditLogMiddleware, RequestIdMiddleware
from app.models.schemas import ErrorResponse
from app.movescout.client import MoveScoutError
from app.routes import appointments, health, leads, queries

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    logger.info("Starting MoveScout Middleware API (env=%s)", settings.environment)
    yield
    logger.info("Shutting down MoveScout Middleware API")


def create_app() -> FastAPI:
    settings = get_settings()

    docs_url = None if settings.disable_public_docs else "/docs"
    redoc_url = None if settings.disable_public_docs else "/redoc"
    openapi_url = None if settings.disable_public_docs else "/openapi.json"

    app = FastAPI(
        title="MoveScout Middleware API",
        description="REST proxy for MoveScout Pro API with API key authentication",
        version="0.1.0",
        lifespan=lifespan,
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
    )

    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuditLogMiddleware)
    app.add_middleware(RequestIdMiddleware)

    @app.exception_handler(MoveScoutError)
    async def movescout_error_handler(request: Request, exc: MoveScoutError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                error=exc.message,
                code=exc.code,
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                error=str(exc.errors()),
                code="VALIDATION_ERROR",
                request_id=request_id,
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error")
        request_id = getattr(request.state, "request_id", None)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="Internal server error",
                code="INTERNAL_ERROR",
                request_id=request_id,
            ).model_dump(),
        )

    app.include_router(health.router)
    app.include_router(leads.router)
    app.include_router(appointments.router)
    app.include_router(queries.router)

    return app


app = create_app()
