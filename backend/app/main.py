"""
FastAPI Application Entry Point.
Configures CORS, registers routes, centralized exception handlers,
and orchestrates database/model lifespan management.
"""

from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.logging import logger
from app.models.base import init_db
from app.ml.model_registry import model_registry
from app.api.routes import (
    auth_router,
    inference_router,
    images_router,
    models_router,
    health_router,
)
from app.utils.validators import ImageValidationError


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting X-Ray to CT Translation API service...")
    # Initialize database tables
    await init_db()
    logger.info("Database initialized successfully.")

    # Pre-warm model in background
    _ = model_registry.get_model()
    logger.info("Model registry ready.")

    yield

    logger.info("Shutting down X-Ray to CT Translation API service...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description=(
        "Production-Grade Medical Image Translation API (X-Ray to CT). "
        "Strictly for educational and research exploration. "
        "Generated images are AI approximations and NOT clinically validated CT scans."
    ),
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# CORS Middleware
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------------------
# Centralized Exception Handlers
# ------------------------------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Formats HTTP exceptions into standard envelope format."""
    code = "HTTP_ERROR"
    message = str(exc.detail)

    if isinstance(exc.detail, dict):
        code = exc.detail.get("code", code)
        message = exc.detail.get("message", message)

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": code,
                "message": message,
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Formats validation errors cleanly without dumping internal schemas."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameter format",
                "details": exc.errors(),
            },
        },
    )


@app.exception_handler(ImageValidationError)
async def image_validation_exception_handler(request: Request, exc: ImageValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message,
            },
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catches unhandled errors without leaking tracebacks to public clients."""
    logger.error(f"Unhandled server error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An internal server error occurred. Please retry or contact support.",
            },
        },
    )


# ------------------------------------------------------------------------------
# API Route Registration
# ------------------------------------------------------------------------------
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(auth_router, prefix=settings.API_PREFIX)
app.include_router(inference_router, prefix=settings.API_PREFIX)
app.include_router(images_router, prefix=settings.API_PREFIX)
app.include_router(models_router, prefix=settings.API_PREFIX)

# ------------------------------------------------------------------------------
# Frontend SPA Static Serving (Production / Unified Container Mode)
# ------------------------------------------------------------------------------
STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
    if (STATIC_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API endpoints or docs
        clean_path = full_path.lstrip("/")
        if clean_path.startswith("api/") or clean_path.startswith("docs") or clean_path == "openapi.json":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API route not found")
        target_file = STATIC_DIR / clean_path
        if target_file.is_file():
            return FileResponse(target_file)
        return FileResponse(STATIC_DIR / "index.html")
else:
    @app.get("/")
    async def root():
        return {
            "project": settings.PROJECT_NAME,
            "docs": f"{settings.API_PREFIX}/docs",
            "health": f"{settings.API_PREFIX}/health",
            "disclaimer": "RESEARCH ONLY - NOT A CLINICAL CT SCAN",
        }
