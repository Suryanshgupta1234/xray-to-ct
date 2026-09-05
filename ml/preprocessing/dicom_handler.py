"""
DICOM Medical Image Handler.
Extracts pixel arrays, computes calibrated Hounsfield Units (HU),
applies radiologic windowing, and enforces strict PHI de-identification.
"""

import io
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, Union
import numpy as np

try:
    import pydicom
    from pydicom.dataset import FileDataset
    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False


class DICOMWindowPresets:
    """Standard clinical CT window center (level) and width presets."""
    MEDIASTINUM_SOFT_TISSUE = {"center": 40, "width": 400}
    LUNG = {"center": -600, "width": 1500}
    BONE = {"center": 400, "width": 1800}
    BRAIN = {"center": 40, "width": 80}
    ABDOMEN = {"center": 50, "width": 350}


# Sensitive Protected Health Information (PHI) DICOM tags that must be stripped
SENSITIVE_PHI_TAGS = [
    "PatientName", "PatientID", "PatientBirthDate", "PatientSex", "PatientAge",
    "PatientAddress", "InsurancePlanIdentification", "OtherPatientIDs",
    "InstitutionName", "InstitutionAddress", "ReferringPhysicianName",
    "PerformingPhysicianName", "OperatorsName", "AccessionNumber",
    "StudyID", "StudyDate", "StudyTime", "SeriesDate", "SeriesTime",
    "AcquisitionDate", "AcquisitionTime", "ContentDate", "ContentTime",
]


def load_dicom_image(
    source: Union[str, Path, bytes, io.BytesIO],
    window: Optional[Dict[str, float]] = None,
    normalize_range: Tuple[float, float] = (-1.0, 1.0),
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load a DICOM file from file path or byte stream, extract pixel array,
    convert to calibrated Hounsfield Units (if CT/applicable), apply windowing,
    and return normalized float32 array along with de-identified metadata.

    Args:
        source: File path, bytes, or BytesIO buffer of the DICOM file.
        window: Dict with 'center' and 'width' for HU windowing.
        normalize_range: Target output range (min, max), default (-1.0, 1.0) for GAN.

    Returns:
        Tuple of (processed_image_array [H, W], sanitized_metadata_dict)
    """
    if not PYDICOM_AVAILABLE:
        raise ImportError(
            "pydicom is required for DICOM processing. "
            "Install it via `pip install pydicom`."
        )

    if isinstance(source, (str, Path)):
        dcm = pydicom.dcmread(str(source))
    elif isinstance(source, (bytes, io.BytesIO)):
        buffer = io.BytesIO(source) if isinstance(source, bytes) else source
        dcm = pydicom.dcmread(buffer)
    else:
        raise TypeError(f"Unsupported source type: {type(source)}")

    # Extract sanitized metadata (stripping PHI)
    metadata = deidentify_dicom_metadata(dcm)

    # Extract raw pixel array
    pixel_array = dcm.pixel_array.astype(np.float32)

    # Apply rescale slope and intercept for Hounsfield Units (HU) calibration
    slope = getattr(dcm, "RescaleSlope", 1.0)
    intercept = getattr(dcm, "RescaleIntercept", 0.0)

    # In CT imaging, HU = pixel_value * slope + intercept
    # In planar projection X-ray, slope/intercept may be 1/0 or missing
    if slope != 1.0 or intercept != 0.0:
        hu_array = pixel_array * float(slope) + float(intercept)
    else:
        hu_array = pixel_array

    # Photometric Interpretation check (handle MONOCHROME1 where 0 is white)
    photo_interp = getattr(dcm, "PhotometricInterpretation", "MONOCHROME2")
    if photo_interp == "MONOCHROME1":
        hu_array = np.max(hu_array) - hu_array

    # Apply HU windowing if specified
    if window is not None:
        processed = apply_hu_window(
            hu_array,
            center=window.get("center", 40),
            width=window.get("width", 400),
            normalize_range=normalize_range,
        )
    else:
        # Default min-max normalization if no specific window requested
        min_val = np.min(hu_array)
        max_val = np.max(hu_array)
        if max_val > min_val:
            scaled = (hu_array - min_val) / (max_val - min_val)
        else:
            scaled = np.zeros_like(hu_array)
        
        # Scale to normalize_range
        low, high = normalize_range
        processed = scaled * (high - low) + low

    return processed.astype(np.float32), metadata


def apply_hu_window(
    hu_array: np.ndarray,
    center: float,
    width: float,
    normalize_range: Tuple[float, float] = (-1.0, 1.0),
) -> np.ndarray:
    """
    Apply radiologic windowing on Hounsfield Units and scale to target range.

    Formula:
        lower_bound = center - (width / 2)
        upper_bound = center + (width / 2)
        clipped = np.clip(hu_array, lower_bound, upper_bound)
    """
    lower = center - (width / 2.0)
    upper = center + (width / 2.0)

    clipped = np.clip(hu_array, lower, upper)
    normalized = (clipped - lower) / max(width, 1e-5)

    low, high = normalize_range
    return normalized * (high - low) + low


def deidentify_dicom_metadata(dcm: Any) -> Dict[str, Any]:
    """
    Extract safe, non-identifying technical metadata from DICOM object,
    strictly stripping HIPAA / PHI identifiers.
    """
    sanitized: Dict[str, Any] = {
        "Modality": getattr(dcm, "Modality", "UNKNOWN"),
        "Rows": getattr(dcm, "Rows", None),
        "Columns": getattr(dcm, "Columns", None),
        "PhotometricInterpretation": getattr(dcm, "PhotometricInterpretation", "UNKNOWN"),
        "PixelSpacing": [float(x) for x in getattr(dcm, "PixelSpacing", [1.0, 1.0])],
        "BitsAllocated": getattr(dcm, "BitsAllocated", None),
        "BitsStored": getattr(dcm, "BitsStored", None),
        "HighBit": getattr(dcm, "HighBit", None),
        "RescaleSlope": float(getattr(dcm, "RescaleSlope", 1.0)),
        "RescaleIntercept": float(getattr(dcm, "RescaleIntercept", 0.0)),
        "WindowCenter": float(dcm.WindowCenter) if hasattr(dcm, "WindowCenter") and not isinstance(dcm.WindowCenter, pydicom.multival.MultiValue) else 40.0,
        "WindowWidth": float(dcm.WindowWidth) if hasattr(dcm, "WindowWidth") and not isinstance(dcm.WindowWidth, pydicom.multival.MultiValue) else 400.0,
        "IsDeidentified": True,
    }
    return sanitized
