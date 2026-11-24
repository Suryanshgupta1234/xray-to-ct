"""
File Upload Security & Image Validation Module.
Treats all uploads as untrusted input. Inspects magic bytes, validates MIME types,
enforces size/dimension constraints, and catches image corruption.
"""

import io
from typing import Tuple, Optional
from PIL import Image

from app.core.config import settings

# Magic byte signatures
MAGIC_SIGNATURES = {
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
    b"DICM": "application/dicom",
}


class ImageValidationError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def validate_uploaded_image(
    file_bytes: bytes,
    original_filename: str,
    max_size_bytes: Optional[int] = None,
    max_dimension: int = 4096,
) -> Tuple[str, Tuple[int, int]]:
    """
    Validates an uploaded image file against security and formatting constraints.

    Returns:
        Tuple[str, Tuple[int, int]]: (detected_format, (width, height))

    Raises:
        ImageValidationError: If validation checks fail.
    """
    limit = max_size_bytes or settings.max_upload_bytes

    # 1. Size constraint check
    if len(file_bytes) == 0:
        raise ImageValidationError("EMPTY_FILE", "Uploaded file is empty (0 bytes).")

    if len(file_bytes) > limit:
        max_mb = limit / (1024 * 1024)
        raise ImageValidationError(
            "FILE_TOO_LARGE",
            f"File size exceeds maximum allowed limit of {max_mb:.1f} MB."
        )

    # 2. Extension check
    filename_lower = original_filename.lower().strip()
    ext = filename_lower.split(".")[-1] if "." in filename_lower else ""

    dangerous_exts = {"exe", "bat", "cmd", "sh", "ps1", "py", "js", "php", "html", "htm", "vbs", "jar"}
    if ext in dangerous_exts:
        raise ImageValidationError(
            "UNSUPPORTED_EXTENSION",
            f"File extension '.{ext}' is prohibited for security."
        )

    if ext and ext not in settings.allowed_extensions_list:
        raise ImageValidationError(
            "UNSUPPORTED_EXTENSION",
            f"Extension '.{ext}' is not supported. Allowed extensions: {settings.ALLOWED_EXTENSIONS}."
        )

    # 3. Format and integrity inspection
    detected_mime = None
    dimensions = (0, 0)

    # Check for DICOM standard header or explicit dicom extension
    is_dicom = False
    if len(file_bytes) > 132 and file_bytes[128:132] == b"DICM":
        is_dicom = True
    elif ext in ("dcm", "dicom"):
        try:
            import pydicom
            pydicom.dcmread(io.BytesIO(file_bytes), stop_before_pixels=True)
            is_dicom = True
        except Exception:
            is_dicom = False

    if is_dicom:
        detected_mime = "application/dicom"
        try:
            import pydicom
            dcm = pydicom.dcmread(io.BytesIO(file_bytes))
            arr = dcm.pixel_array
            dimensions = (arr.shape[1], arr.shape[0])
        except Exception as e:
            raise ImageValidationError("CORRUPT_DICOM", f"Failed to parse DICOM pixel array: {str(e)}")
    else:
        # Standard image formats (JPEG, PNG, WebP, BMP, TIFF, JFIF, AVIF, etc.)
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                img_format = (img.format or "").upper()
                dimensions = img.size

                mime_map = {
                    "PNG": "image/png",
                    "JPEG": "image/jpeg",
                    "MPO": "image/jpeg",
                    "JFIF": "image/jpeg",
                    "WEBP": "image/webp",
                    "BMP": "image/bmp",
                    "TIFF": "image/tiff",
                    "AVIF": "image/avif",
                    "HEIC": "image/heic",
                    "HEIF": "image/heif",
                }
                detected_mime = mime_map.get(
                    img_format,
                    f"image/{img_format.lower()}" if img_format else "image/png"
                )
        except Exception as e:
            raise ImageValidationError(
                "CORRUPT_IMAGE",
                f"Image file is corrupt or unreadable. Please upload a standard photo or radiograph (PNG, JPEG, WebP, DICOM): {str(e)}"
            )

    if not detected_mime:
        raise ImageValidationError(
            "INVALID_MIME_TYPE",
            "File header does not match any allowed medical or standard image format."
        )

    width, height = dimensions
    if width > max_dimension or height > max_dimension:
        raise ImageValidationError(
            "DIMENSION_EXCEEDED",
            f"Image dimensions ({width}x{height}) exceed maximum allowed limit of {max_dimension}px."
        )

    return detected_mime, dimensions
