"""
Image Retrieval & Streaming Endpoint.
Safely serves stored uploads, synthetic CT outputs, and difference maps with MIME headers.
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import Response

from app.services.storage_service import BaseStorageService, get_storage_service

router = APIRouter(prefix="/images", tags=["Images"])


@router.get("/{subfolder}/{filename}")
async def get_stored_image(
    subfolder: str,
    filename: str,
    storage: BaseStorageService = Depends(get_storage_service),
):
    """
    Safely retrieves and streams a stored image asset.
    Enforces path traversal defenses.
    """
    # Guard against directory traversal attacks
    if ".." in subfolder or ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PATH", "message": "Illegal path components detected."},
        )

    allowed_subfolders = {"uploads", "results", "evaluation"}
    if subfolder not in allowed_subfolders:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN_FOLDER", "message": "Access to requested directory is forbidden."},
        )

    asset_key = f"{subfolder}/{filename}"
    try:
        data = await storage.get_file(asset_key)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "IMAGE_NOT_FOUND", "message": f"Asset '{asset_key}' was not found."},
        )

    # Determine Content-Type
    ext = filename.split(".")[-1].lower()
    media_type = "image/png"
    if ext in ("jpg", "jpeg"):
        media_type = "image/jpeg"
    elif ext in ("dcm", "dicom"):
        media_type = "application/dicom"

    return Response(
        content=data,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=86400",
            "X-Content-Type-Options": "nosniff",
        },
    )
