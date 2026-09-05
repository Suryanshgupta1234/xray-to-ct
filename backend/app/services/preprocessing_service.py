"""
Preprocessing Service.
Coordinates file validation and conversion to normalized model tensors.
"""

from typing import Tuple, Dict, Any
import torch

from app.utils.validators import validate_uploaded_image
from ml.preprocessing.transforms import MedicalImagePreprocessor


class PreprocessingService:
    """Validates incoming client payloads and converts them into normalized PyTorch tensors."""

    def __init__(self, target_size: Tuple[int, int] = (256, 256)):
        self.preprocessor = MedicalImagePreprocessor(
            target_size=target_size,
            normalize_range=(-1.0, 1.0),
            in_channels=1,
        )

    def process_upload(
        self,
        file_bytes: bytes,
        original_filename: str,
    ) -> Tuple[torch.Tensor, str, Dict[str, Any]]:
        """
        Validates untrusted upload and returns:
            - normalized PyTorch tensor: (1, 1, H, W)
            - detected format string
            - metadata dictionary
        """
        # Validate format, magic bytes, dimensions, and corruption
        detected_format, dimensions = validate_uploaded_image(file_bytes, original_filename)

        # Convert to model input tensor
        tensor, meta = self.preprocessor.preprocess_image(file_bytes)

        metadata = {
            "original_filename": original_filename,
            "detected_format": detected_format,
            "original_width": dimensions[0],
            "original_height": dimensions[1],
            "processed_shape": list(tensor.shape),
            **meta,
        }

        return tensor, detected_format, metadata
