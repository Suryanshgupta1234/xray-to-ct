"""
API Routes Package.
"""

from app.api.routes.auth import router as auth_router
from app.api.routes.inference import router as inference_router
from app.api.routes.images import router as images_router
from app.api.routes.models import router as models_router
from app.api.routes.health import router as health_router

__all__ = [
    "auth_router",
    "inference_router",
    "images_router",
    "models_router",
    "health_router",
]
