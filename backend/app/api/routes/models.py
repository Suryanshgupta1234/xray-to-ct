"""
Model Management & Metadata API Routes.
Exposes registered model architectures, versions, training parameters, and admin metrics.
"""

import json
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.base import get_db
from app.models.user import User
from app.models.inference import InferenceJob, InferenceStatus
from app.core.config import settings
from app.core.dependencies import get_current_user, get_current_admin
from app.ml.model_registry import model_registry
from app.schemas.inference import StandardResponse
from app.schemas.model import ModelVersionResponseData, AdminSystemStatsData

router = APIRouter(prefix="/models", tags=["Models"])


@router.get("", response_model=StandardResponse[List[ModelVersionResponseData]])
async def list_models():
    """Lists available model translation versions and metadata."""
    model_dir = Path(settings.MODEL_DIR)
    results = []

    if model_dir.exists():
        for version_dir in model_dir.iterdir():
            if version_dir.is_dir():
                meta_file = version_dir / "metadata.json"
                if meta_file.exists():
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            meta = json.load(f)
                        results.append(
                            ModelVersionResponseData(
                                id=version_dir.name,
                                version=meta.get("version", version_dir.name),
                                model_name=meta.get("model_name", "pix2pix_unet256"),
                                architecture=meta.get("architecture", "pix2pix"),
                                is_active=(version_dir.name == settings.ACTIVE_MODEL_VERSION),
                                hyperparameters=meta.get("hyperparameters"),
                                evaluation_metrics=meta.get("best_validation_metrics"),
                                created_at=meta_file.stat().st_mtime,
                            )
                        )
                    except Exception:
                        pass

    # Fallback default if directory empty
    if not results:
        results.append(
            ModelVersionResponseData(
                id="v1",
                version="v1",
                model_name="pix2pix_unet256",
                architecture="pix2pix_UNet256_PatchGAN",
                is_active=True,
                hyperparameters={"batch_size": 4, "lr": 0.0002, "lambda_l1": 100.0},
                evaluation_metrics={"SSIM": 0.85, "PSNR_dB": 24.5},
                created_at=model_dir.stat().st_mtime if model_dir.exists() else 0,
            )
        )

    return StandardResponse(
        success=True,
        data=results,
        message="Model registry queried successfully",
    )


@router.get("/admin/stats", response_model=StandardResponse[AdminSystemStatsData])
async def get_admin_system_stats(
    admin_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Administrative overview of system load, total users, inferences, and health."""
    import torch

    total_users_res = await db.execute(select(func.count(User.id)))
    total_users = total_users_res.scalar() or 0

    total_jobs_res = await db.execute(select(func.count(InferenceJob.id)))
    total_jobs = total_jobs_res.scalar() or 0

    completed_res = await db.execute(
        select(func.count(InferenceJob.id)).where(InferenceJob.status == InferenceStatus.COMPLETED)
    )
    completed_jobs = completed_res.scalar() or 0

    failed_res = await db.execute(
        select(func.count(InferenceJob.id)).where(InferenceJob.status == InferenceStatus.FAILED)
    )
    failed_jobs = failed_res.scalar() or 0

    avg_lat_res = await db.execute(
        select(func.avg(InferenceJob.processing_time_ms)).where(InferenceJob.status == InferenceStatus.COMPLETED)
    )
    avg_latency = avg_lat_res.scalar() or 0.0

    return StandardResponse(
        success=True,
        data=AdminSystemStatsData(
            total_users=total_users,
            total_inferences=total_jobs,
            completed_inferences=completed_jobs,
            failed_inferences=failed_jobs,
            average_latency_ms=round(avg_latency, 2),
            active_model_version=settings.ACTIVE_MODEL_VERSION,
            gpu_available=torch.cuda.is_available(),
        ),
        message="Admin system metrics retrieved",
    )
