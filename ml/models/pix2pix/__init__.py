"""
pix2pix Conditional GAN Translation Module.
Combines UNetGenerator and PatchGANDiscriminator into a unified BaseTranslationModel interface.
"""

from typing import Dict, Any, Optional
import torch
import torch.nn as nn

from ml.models.base import BaseTranslationModel
from ml.models.pix2pix.generator import UNetGenerator
from ml.models.pix2pix.discriminator import PatchGANDiscriminator


class Pix2PixModel(BaseTranslationModel):
    """
    Complete pix2pix translation system adhering to the BaseTranslationModel interface.
    """

    def __init__(self, in_channels: int = 1, out_channels: int = 1):
        super().__init__(in_channels=in_channels, out_channels=out_channels)
        self.generator = UNetGenerator(in_channels=in_channels, out_channels=out_channels)
        self.discriminator = PatchGANDiscriminator(in_channels=in_channels, out_channels=out_channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Inference forward pass: produces synthetic CT representation from X-ray."""
        return self.generator(x)

    def get_generator(self) -> nn.Module:
        return self.generator

    def get_discriminator(self) -> Optional[nn.Module]:
        return self.discriminator

    def get_model_metadata(self) -> Dict[str, Any]:
        return {
            "model_name": "pix2pix_conditional_gan",
            "generator_architecture": "UNet256_SkipConnections",
            "discriminator_architecture": "PatchGAN_70x70",
            "in_channels": self.in_channels,
            "out_channels": self.out_channels,
            "latent_resolution": [256, 256],
            "norm_range": [-1.0, 1.0],
        }


__all__ = ["UNetGenerator", "PatchGANDiscriminator", "Pix2PixModel"]
