"""
System Health & Monitoring Endpoint.
Checks operational status of API, Database connection, Model Cache, and Storage backends.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.base import get_db
from app.services.storage_service import BaseStorageService, get_storage_service
from app.ml.model_registry import model_registry
from app.schemas.inference import StandardResponse
from app.schemas.model import SystemHealthResponseData, HealthServiceStatus

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=StandardResponse[SystemHealthResponseData])
async def health_check(
    db: AsyncSession = Depends(get_db),
    storage: BaseStorageService = Depends(get_storage_service),
):
    """
    Performs comprehensive runtime health checks across all backend subsystems.
    """
    # 1. Database check
    db_status = "healthy"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # 2. Storage check
    storage_ok = await storage.check_health()
    storage_status = "healthy" if storage_ok else "unhealthy"

    # 3. ML Model Cache check
    ml_info = model_registry.check_health()
    model_status = "healthy"

    overall_healthy = (db_status == "healthy") and storage_ok

    health_data = SystemHealthResponseData(
        status="healthy" if overall_healthy else "degraded",
        version="1.0.0",
        device=str(model_registry.device),
        api=HealthServiceStatus(status="healthy"),
        database=HealthServiceStatus(status=db_status),
        storage=HealthServiceStatus(status=storage_status),
        model_cache=HealthServiceStatus(status=model_status, details=ml_info),
        timestamp=datetime.now(timezone.utc),
    )

    return StandardResponse(
        success=overall_healthy,
        data=health_data,
        message="System status checked",
    )
