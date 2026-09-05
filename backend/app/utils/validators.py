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
    filename_lower = original_filename.lower()
    ext = filename_lower.split(".")[-1] if "." in filename_lower else ""
    if ext not in settings.allowed_extensions_list:
        raise ImageValidationError(
            "UNSUPPORTED_EXTENSION",
            f"Extension '.{ext}' is not supported. Allowed extensions: {settings.ALLOWED_EXTENSIONS}."
        )

    # 3. Magic Byte Inspection (Anti-spoofing)
    detected_mime = None
    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_mime = "image/png"
    elif file_bytes.startswith(b"\xff\xd8\xff"):
        detected_mime = "image/jpeg"
    elif len(file_bytes) > 132 and file_bytes[128:132] == b"DICM":
        detected_mime = "application/dicom"

    # Fallback check for DICOM preamble omission
    if ext in ("dcm", "dicom") and detected_mime is None:
        try:
            import pydicom
            pydicom.dcmread(io.BytesIO(file_bytes), stop_before_pixels=True)
            detected_mime = "application/dicom"
        except Exception:
            pass

    if not detected_mime:
        raise ImageValidationError(
            "INVALID_MIME_TYPE",
            "File header does not match any allowed medical or standard image format."
        )

    # 4. Integrity and dimension validation
    dimensions = (0, 0)
    if detected_mime == "application/dicom":
        try:
            import pydicom
            dcm = pydicom.dcmread(io.BytesIO(file_bytes))
            arr = dcm.pixel_array
            dimensions = (arr.shape[1], arr.shape[0])
        except Exception as e:
            raise ImageValidationError("CORRUPT_DICOM", f"Failed to parse DICOM pixel array: {str(e)}")
    else:
        try:
            with Image.open(io.BytesIO(file_bytes)) as img:
                img.verify()
            # Re-open after verify() to inspect dimensions
            with Image.open(io.BytesIO(file_bytes)) as img:
                dimensions = img.size
        except Exception as e:
            raise ImageValidationError("CORRUPT_IMAGE", f"Image file is corrupt or unreadable: {str(e)}")

    width, height = dimensions
    if width > max_dimension or height > max_dimension:
        raise ImageValidationError(
            "DIMENSION_EXCEEDED",
            f"Image dimensions ({width}x{height}) exceed maximum allowed limit of {max_dimension}px."
        )

    return detected_mime, dimensions
