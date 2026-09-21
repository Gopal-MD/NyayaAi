"""NyayaAi FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.db import create_tables
from app.core.logging import setup_logging, get_logger
from app.core.security import RequestIDMiddleware, limiter

# Routers
from app.api import auth, cases, chat, documents, search, actions, referrals, deadlines, feedback, voice

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("nyayaai_starting", env=settings.APP_ENV)
    await create_tables()
    logger.info("database_ready")
    yield
    logger.info("nyayaai_shutdown")


app = FastAPI(
    title="NyayaAi API",
    description="AI legal information and document-understanding platform for India",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_ENV != "production" else None,
    redoc_url=None,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestIDMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "An unexpected error occurred."},
    )


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "0.1.0", "env": settings.APP_ENV}


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(cases.router, prefix="/cases", tags=["cases"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(search.router, tags=["search"])
app.include_router(actions.router, prefix="/action-plan", tags=["action-plan"])
app.include_router(referrals.router, prefix="/referrals", tags=["referrals"])
app.include_router(deadlines.router, prefix="/deadlines", tags=["deadlines"])
app.include_router(feedback.router, prefix="/feedback", tags=["feedback"])
app.include_router(voice.router, prefix="/voice", tags=["voice"])
