"""
70x70 PatchGAN Discriminator Architecture for Conditional GAN Translation.
Classifies NxN local image patches as real or fake, penalizing high-frequency
artifacts and enforcing structural edge sharpness.
"""

import torch
import torch.nn as nn
from ml.models.pix2pix.networks import weights_init_normal


class PatchGANDiscriminator(nn.Module):
    """
    70x70 PatchGAN Discriminator.
    Takes concatenated condition (X-ray) and target (CT or generated CT),
    and outputs a 2D grid of patch logits (approx 30x30 for 256x256 inputs).
    """

    def __init__(self, in_channels: int = 1, out_channels: int = 1):
        super().__init__()
        # Discriminator receives condition concatenated with target
        total_input_channels = in_channels + out_channels

        def discriminator_block(
            in_filters: int,
            out_filters: int,
            stride: int = 2,
            normalization: bool = True,
        ) -> list:
            """Layer block: Conv2d -> [BatchNorm2d] -> LeakyReLU(0.2)"""
            layers = [
                nn.Conv2d(
                    in_filters,
                    out_filters,
                    kernel_size=4,
                    stride=stride,
                    padding=1,
                    bias=not normalization,
                )
            ]
            if normalization:
                layers.append(nn.BatchNorm2d(out_filters))
            layers.append(nn.LeakyReLU(0.2, inplace=True))
            return layers

        self.model = nn.Sequential(
            # Stage 1: 256x256 -> 128x128 (No normalization on first layer)
            *discriminator_block(total_input_channels, 64, stride=2, normalization=False),
            # Stage 2: 128x128 -> 64x64
            *discriminator_block(64, 128, stride=2, normalization=True),
            # Stage 3: 64x64 -> 32x32
            *discriminator_block(128, 256, stride=2, normalization=True),
            # Stage 4: 32x32 -> 31x31 (stride=1, padding=1)
            *discriminator_block(256, 512, stride=1, normalization=True),
            # Stage 5: Final 1-channel prediction patch map (30x30 logits)
            nn.Conv2d(512, 1, kernel_size=4, stride=1, padding=1),
        )

        self.apply(weights_init_normal)

    def forward(self, condition: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
        """
        Args:
            condition: Condition tensor (X-ray), shape (B, in_channels, H, W)
            target: Target tensor (Real or Synthetic CT), shape (B, out_channels, H, W)

        Returns:
            Logits tensor of patch predictions, shape (B, 1, H', W')
        """
        img_input = torch.cat([condition, target], dim=1)
        return self.model(img_input)
