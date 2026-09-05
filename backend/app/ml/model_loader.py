"""
Model Loader for loading generator checkpoints into memory.
"""

import sys
from pathlib import Path
from typing import Optional, Tuple
import torch

# Ensure ml core library is discoverable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.models.pix2pix.generator import UNetGenerator
from app.core.logging import logger


def load_generator_weights(
    weights_path: str,
    device: torch.device,
    in_channels: int = 1,
    out_channels: int = 1,
) -> UNetGenerator:
    """
    Instantiates the U-Net 256 generator and loads weights from state dictionary.
    """
    generator = UNetGenerator(in_channels=in_channels, out_channels=out_channels)
    path = Path(weights_path)

    if not path.exists():
        logger.warning(f"Checkpoint not found at '{weights_path}'. Initializing random weights.")
    else:
        logger.info(f"Loading generator weights from {path.resolve()} onto {device}")
        checkpoint = torch.load(str(path), map_location=device)
        if isinstance(checkpoint, dict) and "generator_state_dict" in checkpoint:
            generator.load_state_dict(checkpoint["generator_state_dict"])
        elif isinstance(checkpoint, dict):
            generator.load_state_dict(checkpoint)
        else:
            raise ValueError(f"Unrecognized checkpoint format in {weights_path}")

    generator.to(device)
    generator.eval()
    return generator
