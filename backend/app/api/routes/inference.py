"""
Inference API Routes.
Exposes endpoints for submitting translation jobs, checking job status,
retrieving historical outputs, and managing user job records.
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.base import get_db
from app.models.user import User
from app.models.inference import InferenceJob
from app.core.dependencies import get_current_user
from app.services.inference_service import InferenceService
from app.services.storage_service import get_storage_service, BaseStorageService
from app.schemas.inference import (
    StandardResponse,
    InferenceJobResponseData,
    InferenceListResponseData,
)
from app.utils.validators import ImageValidationError

router = APIRouter(prefix="/inference", tags=["Inference"])


@router.post("", response_model=StandardResponse[InferenceJobResponseData], status_code=status.HTTP_200_OK)
async def create_inference(
    file: UploadFile = File(..., description="2D Planar X-ray image (PNG, JPEG, or DICOM)"),
    model_version: Optional[str] = Form(None, description="Optional target model version, e.g. 'v1'"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: BaseStorageService = Depends(get_storage_service),
):
    """
    Submits a 2D X-ray for AI image-to-image translation.
    Generates synthetic CT-like cross-sectional representation.
    """
    try:
        content = await file.read()
        filename = file.filename or "upload.png"

        service = InferenceService(db=db, storage=storage)
        result = await service.execute_translation(
            user_id=current_user.id,
            file_bytes=content,
            filename=filename,
            model_version=model_version,
        )

        return StandardResponse(
            success=True,
            data=result,
            message="X-Ray to CT translation generated successfully",
        )

    except ImageValidationError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": ve.code, "message": ve.message},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "INFERENCE_ERROR", "message": f"Translation failed: {str(e)}"},
        )


@router.get("/history", response_model=StandardResponse[InferenceListResponseData])
async def get_inference_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: BaseStorageService = Depends(get_storage_service),
):
    """Retrieves paginated history of translations for the current user."""
    offset = (page - 1) * page_size

    total_query = select(func.count(InferenceJob.id)).where(InferenceJob.user_id == current_user.id)
    total_res = await db.execute(total_query)
    total_count = total_res.scalar() or 0

    jobs_query = (
        select(InferenceJob)
        .where(InferenceJob.user_id == current_user.id)
        .order_by(desc(InferenceJob.created_at))
        .offset(offset)
        .limit(page_size)
    )
    res = await db.execute(jobs_query)
    jobs = res.scalars().all()

    items = []
    service = InferenceService(db=db, storage=storage)
    for j in jobs:
        items.append(service._build_response_data(j))

    return StandardResponse(
        success=True,
        data=InferenceListResponseData(
            items=items,
            total=total_count,
            page=page,
            page_size=page_size,
        ),
        message="Inference history retrieved",
    )


@router.get("/{id}", response_model=StandardResponse[InferenceJobResponseData])
async def get_inference_by_id(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: BaseStorageService = Depends(get_storage_service),
):
    """Retrieves a single inference job by its ID."""
    query = select(InferenceJob).where(InferenceJob.id == id, InferenceJob.user_id == current_user.id)
    res = await db.execute(query)
    job = res.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": f"Inference job '{id}' not found."},
        )

    service = InferenceService(db=db, storage=storage)
    return StandardResponse(
        success=True,
        data=service._build_response_data(job),
        message="Inference record found",
    )


@router.delete("/{id}", response_model=StandardResponse[Dict[str, str]])
async def delete_inference_by_id(
    id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    storage: BaseStorageService = Depends(get_storage_service),
):
    """Deletes an inference job and its stored artifacts."""
    query = select(InferenceJob).where(InferenceJob.id == id, InferenceJob.user_id == current_user.id)
    res = await db.execute(query)
    job = res.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "JOB_NOT_FOUND", "message": f"Inference job '{id}' not found."},
        )

    # Clean stored files
    if job.input_image_path:
        await storage.delete_file(job.input_image_path)
    if job.output_image_path:
        await storage.delete_file(job.output_image_path)

    await db.delete(job)
    await db.commit()

    return StandardResponse(
        success=True,
        data={"deleted_id": id},
        message="Inference job deleted successfully",
    )
