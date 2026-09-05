"""
Image Transformation and Preprocessing Utilities.
Handles standard image format parsing (PNG, JPEG), DICOM routing,
bidirectional tensor conversions, and GAN normalization [-1, 1].
"""

import io
from pathlib import Path
from typing import Union, Tuple, Optional
import numpy as np
from PIL import Image
import torch

from ml.preprocessing.dicom_handler import load_dicom_image, PYDICOM_AVAILABLE


class MedicalImagePreprocessor:
    """
    Standard preprocessor for 2D medical and scientific images.
    Converts inputs into normalized PyTorch tensors suitable for pix2pix translation.
    """

    def __init__(
        self,
        target_size: Tuple[int, int] = (256, 256),
        normalize_range: Tuple[float, float] = (-1.0, 1.0),
        in_channels: int = 1,
    ):
        self.target_size = target_size
        self.normalize_range = normalize_range
        self.in_channels = in_channels

    def preprocess_image(
        self,
        source: Union[str, Path, bytes, io.BytesIO, Image.Image],
    ) -> Tuple[torch.Tensor, dict]:
        """
        Loads and transforms an image (PNG, JPEG, or DICOM) to a PyTorch tensor.

        Returns:
            Tuple[torch.Tensor, dict]:
                - Tensor of shape (1, C, H, W) normalized to target_range.
                - Metadata dict (original format, dimensions, mode).
        """
        metadata = {}

        # 1. Handle PIL Image
        if isinstance(source, Image.Image):
            pil_img = source.convert("L" if self.in_channels == 1 else "RGB")
            metadata["original_format"] = "PIL"
            metadata["original_size"] = pil_img.size

        # 2. Handle DICOM bytes or path
        elif self._is_dicom(source):
            np_arr, dcm_meta = load_dicom_image(
                source, normalize_range=self.normalize_range
            )
            metadata.update(dcm_meta)
            metadata["original_format"] = "DICOM"
            metadata["original_size"] = (np_arr.shape[1], np_arr.shape[0])

            # Convert numpy array directly to tensor
            img_tensor = torch.from_numpy(np_arr).float()
            if img_tensor.ndim == 2:
                img_tensor = img_tensor.unsqueeze(0)  # (1, H, W)

            # Resize if needed
            if (img_tensor.shape[1], img_tensor.shape[2]) != self.target_size:
                img_tensor = torch.nn.functional.interpolate(
                    img_tensor.unsqueeze(0),
                    size=self.target_size,
                    mode="bicubic",
                    align_corners=False,
                ).squeeze(0)

            # Add batch dimension: (1, C, H, W)
            return img_tensor.unsqueeze(0), metadata

        # 3. Handle File Path
        elif isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"Image file not found: {source}")
            with Image.open(path) as img:
                pil_img = img.convert("L" if self.in_channels == 1 else "RGB")
                metadata["original_format"] = img.format or path.suffix
                metadata["original_size"] = img.size

        # 4. Handle raw bytes or BytesIO
        elif isinstance(source, (bytes, io.BytesIO)):
            buffer = io.BytesIO(source) if isinstance(source, bytes) else source
            with Image.open(buffer) as img:
                pil_img = img.convert("L" if self.in_channels == 1 else "RGB")
                metadata["original_format"] = img.format or "BYTES"
                metadata["original_size"] = img.size
        else:
            raise TypeError(f"Unsupported image input type: {type(source)}")

        # Resize PIL image with high-quality Lanczos/Bicubic filter
        resized_img = pil_img.resize(self.target_size, Image.Resampling.BICUBIC)

        # Convert to numpy and normalize to target_range
        arr = np.array(resized_img, dtype=np.float32)
        if arr.ndim == 2:
            arr = arr[:, :, np.newaxis]  # (H, W, 1)

        # Normalization [0, 255] -> [low, high]
        low, high = self.normalize_range
        arr_norm = (arr / 255.0) * (high - low) + low

        # Transpose to (C, H, W) and convert to Tensor
        tensor = torch.from_numpy(arr_norm).permute(2, 0, 1).float()
        return tensor.unsqueeze(0), metadata

    def _is_dicom(self, source: Union[str, Path, bytes, io.BytesIO, Image.Image]) -> bool:
        """Check if source represents a DICOM file."""
        if not PYDICOM_AVAILABLE:
            return False

        if isinstance(source, (str, Path)):
            p = str(source).lower()
            if p.endswith((".dcm", ".dicom")):
                return True
            try:
                with open(source, "rb") as f:
                    f.seek(128)
                    return f.read(4) == b"DICM"
            except Exception:
                return False

        if isinstance(source, bytes):
            return len(source) > 132 and source[128:132] == b"DICM"

        if isinstance(source, io.BytesIO):
            pos = source.tell()
            source.seek(128)
            magic = source.read(4)
            source.seek(pos)
            return magic == b"DICM"

        return False


def tensor_to_pil(
    tensor: torch.Tensor,
    normalize_range: Tuple[float, float] = (-1.0, 1.0),
) -> Image.Image:
    """
    Converts a PyTorch tensor (shape (C, H, W) or (1, C, H, W)) into a PIL Image.
    Denormalizes from [-1.0, 1.0] to [0, 255].
    """
    if tensor.ndim == 4:
        tensor = tensor.squeeze(0)  # Remove batch dim -> (C, H, W)

    tensor = tensor.detach().cpu().float()

    low, high = normalize_range
    # Map from [low, high] to [0, 1]
    norm_0_1 = (tensor - low) / (high - low)
    clipped = torch.clamp(norm_0_1, 0.0, 1.0)
    uint8_tensor = (clipped * 255.0).to(torch.uint8)

    arr = uint8_tensor.numpy()
    if arr.shape[0] == 1:
        # Grayscale (H, W)
        return Image.fromarray(arr[0], mode="L")
    elif arr.shape[0] == 3:
        # RGB (H, W, 3)
        return Image.fromarray(np.transpose(arr, (1, 2, 0)), mode="RGB")
    else:
        raise ValueError(f"Unsupported channel count: {arr.shape[0]}")


def pil_to_tensor(
    img: Image.Image,
    target_size: Tuple[int, int] = (256, 256),
    normalize_range: Tuple[float, float] = (-1.0, 1.0),
    channels: int = 1,
) -> torch.Tensor:
    """Quick helper to convert PIL Image to normalized PyTorch Tensor (1, C, H, W)."""
    preprocessor = MedicalImagePreprocessor(
        target_size=target_size,
        normalize_range=normalize_range,
        in_channels=channels,
    )
    tensor, _ = preprocessor.preprocess_image(img)
    return tensor
