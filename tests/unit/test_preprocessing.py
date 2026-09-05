"""
Unit Tests for Medical Preprocessing, DICOM Windowing, and Image Utilities.
"""

import io
import sys
from pathlib import Path
import pytest
import numpy as np
from PIL import Image
import torch

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ml.preprocessing.transforms import (
    MedicalImagePreprocessor,
    tensor_to_pil,
    pil_to_tensor,
)
from ml.preprocessing.dicom_handler import apply_hu_window, DICOMWindowPresets
from app.utils.validators import validate_uploaded_image, ImageValidationError


def test_preprocessor_with_pil():
    """Validates PIL image conversion to normalized PyTorch tensor."""
    preprocessor = MedicalImagePreprocessor(target_size=(256, 256), in_channels=1)

    raw_img = Image.new("L", (512, 400), color=128)
    tensor, meta = preprocessor.preprocess_image(raw_img)

    assert tensor.shape == (1, 1, 256, 256)
    assert tensor.min().item() >= -1.01
    assert tensor.max().item() <= 1.01
    assert meta["original_size"] == (512, 400)


def test_tensor_to_pil_roundtrip():
    """Validates bidirectional tensor-to-PIL reconstruction."""
    original_arr = np.full((256, 256), 200, dtype=np.uint8)
    original_pil = Image.fromarray(original_arr, mode="L")

    tensor = pil_to_tensor(original_pil)
    reconstructed_pil = tensor_to_pil(tensor)

    rec_arr = np.array(reconstructed_pil)
    # Reconstructed pixel values should match within 1 gray level of precision
    assert np.all(np.abs(rec_arr.astype(int) - original_arr.astype(int)) <= 2)


def test_hu_windowing_formula():
    """Verifies Hounsfield Unit clipping and window transformation."""
    # Create test HU array with values spanning air (-1000) to bone (+1000)
    hu = np.array([-1000.0, 40.0, 1000.0], dtype=np.float32)

    # Soft tissue window: center 40, width 400 -> bounds [-160, 240]
    windowed = apply_hu_window(
        hu,
        center=DICOMWindowPresets.MEDIASTINUM_SOFT_TISSUE["center"],
        width=DICOMWindowPresets.MEDIASTINUM_SOFT_TISSUE["width"],
        normalize_range=(-1.0, 1.0),
    )

    # -1000 is below -160 -> clipped to lower bound -> maps to -1.0
    assert windowed[0] == pytest.approx(-1.0, abs=1e-3)
    # 40 is exact center -> maps to 0.0
    assert windowed[1] == pytest.approx(0.0, abs=1e-3)
    # 1000 is above 240 -> clipped to upper bound -> maps to +1.0
    assert windowed[2] == pytest.approx(1.0, abs=1e-3)


def test_upload_validator_magic_bytes():
    """Verifies rejection of spoofed files and acceptance of valid PNGs."""
    # Valid PNG image bytes
    buf = io.BytesIO()
    Image.new("L", (100, 100), color=50).save(buf, format="PNG")
    valid_png = buf.getvalue()

    mime, dims = validate_uploaded_image(valid_png, "chest_xray.png")
    assert mime == "image/png"
    assert dims == (100, 100)

    # Spoofed file: extension is .png, but content is arbitrary text
    with pytest.raises(ImageValidationError) as exc:
        validate_uploaded_image(b"fake text pretending to be png", "spoofed.png")
    assert exc.value.code == "INVALID_MIME_TYPE"
