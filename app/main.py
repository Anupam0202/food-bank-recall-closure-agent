from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.api import demo, health, incidents, ingestion, media, pubsub, tasks
from app.config import settings
from app.domain.exceptions import AuthorizationError, DomainError, UnsafeActionError, ValidationError
from app.logging_config import configure_logging
from app.web import routes as web_routes

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application started", extra={"event_type": "startup", "outcome": "ready", "ai_mode": settings.ai_label, "repository": settings.repository_label, "media": settings.media_label})
    yield
    logger.info("Application stopped", extra={"event_type": "shutdown", "outcome": "complete"})


app = FastAPI(
    title="Food-Bank Recall Closure Operations",
    description="Internal recall-response coordination prototype; not an official recall lifecycle system.",
    version="1.3.0",
    docs_url="/docs" if settings.app_env in {"development", "test"} else None,
    redoc_url=None,
    lifespan=lifespan,
)
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret, same_site="lax", https_only=settings.secure_http, max_age=8 * 60 * 60)

BASE = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE / "static")), name="static")

app.include_router(health.router)
app.include_router(demo.router)
app.include_router(incidents.router)
app.include_router(ingestion.router)
app.include_router(tasks.router)
app.include_router(media.router)
app.include_router(pubsub.router)
app.include_router(web_routes.router)


@app.exception_handler(AuthorizationError)
async def authorization_error_handler(request: Request, exc: AuthorizationError):
    return JSONResponse(status_code=403, content={"error": "authorization_error", "detail": str(exc)})


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"error": "validation_error", "detail": str(exc)})


@app.exception_handler(UnsafeActionError)
async def unsafe_action_handler(request: Request, exc: UnsafeActionError):
    return JSONResponse(status_code=400, content={"error": "unsafe_action", "detail": str(exc)})


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError):
    return JSONResponse(status_code=400, content={"error": type(exc).__name__, "detail": str(exc)})


@app.middleware("http")
async def request_observability_and_security(request: Request, call_next):
    started = perf_counter()
    incoming = request.headers.get("X-Correlation-ID", "")
    correlation_id = incoming[:80] if incoming.replace("-", "").isalnum() else f"corr_{uuid4().hex[:16]}"
    request.state.correlation_id = correlation_id
    try:
        response = await call_next(request)
        outcome, error_category = "success", None
    except Exception as exc:
        outcome, error_category = "error", type(exc).__name__
        logger.exception("Request failed", extra={"correlation_id": correlation_id, "route": request.url.path, "event_type": "request", "outcome": outcome, "error_category": error_category})
        raise
    duration_ms = int((perf_counter() - started) * 1000)
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
    if settings.secure_http:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    logger.info("Request completed", extra={"correlation_id": correlation_id, "route": request.url.path, "event_type": "request", "duration_ms": duration_ms, "outcome": outcome})
    return response
