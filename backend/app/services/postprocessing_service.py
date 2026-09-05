"""
Postprocessing Service.
Converts synthetic model tensors back into standard viewable images (PNG/JPEG),
computes difference maps, and packages metadata.
"""

import io
from typing import Tuple, Optional
from PIL import Image
import torch

from ml.preprocessing.transforms import tensor_to_pil
from app.utils.image_utils import generate_difference_heatmap, pil_to_base64


class PostprocessingService:
    """Transforms raw PyTorch tensor predictions into client-ready visual artifacts."""

    def __init__(self, normalize_range: Tuple[float, float] = (-1.0, 1.0)):
        self.normalize_range = normalize_range

    def process_prediction(
        self,
        pred_tensor: torch.Tensor,
        input_tensor: Optional[torch.Tensor] = None,
    ) -> Tuple[bytes, Optional[bytes], Image.Image]:
        """
        Converts model output tensor to PNG bytes and generates an error heatmap.

        Returns:
            Tuple:
                - output_png_bytes
                - difference_map_bytes (if input_tensor provided)
                - pil_image
        """
        pil_pred = tensor_to_pil(pred_tensor, normalize_range=self.normalize_range)

        # Convert to PNG byte stream
        buf = io.BytesIO()
        pil_pred.save(buf, format="PNG")
        output_bytes = buf.getvalue()

        diff_bytes = None
        if input_tensor is not None:
            pil_input = tensor_to_pil(input_tensor, normalize_range=self.normalize_range)
            diff_img = generate_difference_heatmap(pil_input, pil_pred)
            buf_diff = io.BytesIO()
            diff_img.save(buf_diff, format="PNG")
            diff_bytes = buf_diff.getvalue()

        return output_bytes, diff_bytes, pil_pred
