"""ResearchOps FastAPI Backend Entrypoint."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.routers import health

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("researchops")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown events."""
    settings = get_settings()
    logger.info("Starting ResearchOps Backend (Environment: %s)", settings.environment)
    missing = settings.check_missing_required_keys()
    if missing:
        logger.warning(
            "External research integrations unconfigured: %s. "
            "Configure them in backend/.env before running live research jobs.",
            ", ".join(missing),
        )
    else:
        logger.info("External research integrations configured and ready.")
    yield
    logger.info("Shutting down ResearchOps Backend.")


app = FastAPI(
    title="ResearchOps API",
    description="Autonomous Research Agent Backend — GATEWAYS 2026",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle application value and validation errors cleanly."""
    logger.warning("Validation error on %s: %s", request.url.path, str(exc))
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error_type": "ValueError"},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions and return structured JSON."""
    logger.error("Unhandled exception on %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred.", "error_type": "InternalServerError"},
    )


@app.get("/")
async def root():
    """Root status endpoint."""
    return {
        "service": "ResearchOps API",
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }


# Include Routers
app.include_router(health.router)
