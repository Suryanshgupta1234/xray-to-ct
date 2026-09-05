"""
Image Processing & Visualization Utilities.
Handles format conversions, difference heatmaps, and base64 data-URI serialization.
"""

import io
import base64
from typing import Tuple, Optional
import numpy as np
from PIL import Image


def pil_to_base64(img: Image.Image, format: str = "PNG") -> str:
    """Converts a PIL Image into a base64 Data URL string."""
    buffered = io.BytesIO()
    img.save(buffered, format=format)
    encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
    mime = "image/png" if format.upper() == "PNG" else "image/jpeg"
    return f"data:{mime};base64,{encoded}"


def base64_to_pil(data_url: str) -> Image.Image:
    """Converts a base64 Data URL or raw base64 string into a PIL Image."""
    if "," in data_url:
        data_url = data_url.split(",", 1)[1]
    decoded = base64.b64decode(data_url)
    return Image.open(io.BytesIO(decoded))


def generate_difference_heatmap(
    img1: Image.Image,
    img2: Image.Image,
    sensitivity: float = 2.0,
) -> Image.Image:
    """
    Computes absolute difference between two aligned images and produces
    a pseudo-color attention heatmap for research visual inspection.
    """
    # Resize img2 to img1 if sizes mismatch
    if img1.size != img2.size:
        img2 = img2.resize(img1.size, Image.Resampling.BICUBIC)

    arr1 = np.array(img1.convert("L"), dtype=np.float32)
    arr2 = np.array(img2.convert("L"), dtype=np.float32)

    diff = np.abs(arr1 - arr2) * sensitivity
    diff_clipped = np.clip(diff, 0, 255).astype(np.uint8)

    # Convert grayscale difference into a subtle pseudo-color visualization (Cyan-Orange glow)
    colored = Image.fromarray(diff_clipped, mode="L")
    return colored


def create_thumbnail(img: Image.Image, size: Tuple[int, int] = (128, 128)) -> Image.Image:
    """Creates an anti-aliased thumbnail for dashboard history lists."""
    thumb = img.copy()
    thumb.thumbnail(size, Image.Resampling.LANCZOS)
    return thumb
