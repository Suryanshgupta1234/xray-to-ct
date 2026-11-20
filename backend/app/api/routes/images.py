"""
Image Retrieval & Streaming Endpoint.
Safely serves stored uploads, synthetic CT outputs, and difference maps with MIME headers.
"""

from pathlib import Path
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import Response

from app.services.storage_service import BaseStorageService, get_storage_service

router = APIRouter(prefix="/images", tags=["Images"])


@router.get("/{file_path:path}")
async def get_stored_image(
    file_path: str,
    storage: BaseStorageService = Depends(get_storage_service),
):
    """
    Safely retrieves and streams a stored image asset.
    Supports nested subfolders (such as slices/<job_id>/<filename.png>).
    Enforces path traversal defenses and folder restrictions.
    """
    # Guard against directory traversal attacks
    if ".." in file_path or "\\" in file_path or file_path.startswith("/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PATH", "message": "Illegal path components detected."},
        )

    parts = file_path.split("/")
    first_folder = parts[0]
    allowed_subfolders = {"uploads", "results", "evaluation", "slices"}
    if first_folder not in allowed_subfolders:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN_FOLDER", "message": "Access to requested directory is forbidden."},
        )

    try:
        data = await storage.get_file(file_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "IMAGE_NOT_FOUND", "message": f"Asset '{file_path}' was not found."},
        )

    # Determine Content-Type
    filename = parts[-1]
    ext = filename.split(".")[-1].lower() if "." in filename else "png"
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
