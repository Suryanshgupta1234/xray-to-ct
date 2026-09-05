"""
U-Net Generator Architecture for pix2pix Image Translation.
Features 8-stage hierarchical encoder-decoder with skip connections
to preserve high-frequency anatomical boundaries.
"""

import torch
import torch.nn as nn
from ml.models.pix2pix.networks import UNetDown, UNetUp, weights_init_normal


class UNetGenerator(nn.Module):
    """
    U-Net 256 Generator with Skip Connections.
    Takes condition image (e.g. 2D X-ray) and synthesizes target representation (CT slice).
    Output is bounded in [-1.0, 1.0] via Tanh activation.
    """

    def __init__(self, in_channels: int = 1, out_channels: int = 1):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels

        # Encoder (Downsampling)
        self.down1 = UNetDown(in_channels, 64, normalize=False)  # 256 -> 128
        self.down2 = UNetDown(64, 128)                          # 128 -> 64
        self.down3 = UNetDown(128, 256)                         # 64 -> 32
        self.down4 = UNetDown(256, 512)                         # 32 -> 16
        self.down5 = UNetDown(512, 512)                         # 16 -> 8
        self.down6 = UNetDown(512, 512)                         # 8 -> 4
        self.down7 = UNetDown(512, 512)                         # 4 -> 2
        self.down8 = UNetDown(512, 512, normalize=False)        # 2 -> 1 (Bottleneck)

        # Decoder (Upsampling with Skip Connections)
        self.up1 = UNetUp(512, 512, dropout=0.5)                 # 1 -> 2 (+ d7 -> 1024)
        self.up2 = UNetUp(1024, 512, dropout=0.5)                # 2 -> 4 (+ d6 -> 1024)
        self.up3 = UNetUp(1024, 512, dropout=0.5)                # 4 -> 8 (+ d5 -> 1024)
        self.up4 = UNetUp(1024, 512)                            # 8 -> 16 (+ d4 -> 1024)
        self.up5 = UNetUp(1024, 256)                            # 16 -> 32 (+ d3 -> 512)
        self.up6 = UNetUp(512, 128)                             # 32 -> 64 (+ d2 -> 256)
        self.up7 = UNetUp(256, 64)                              # 64 -> 128 (+ d1 -> 128)

        # Final reconstruction layer
        self.final = nn.Sequential(
            nn.Upsample(scale_factor=2),
            nn.ZeroPad2d((1, 0, 1, 0)),
            nn.Conv2d(128, out_channels, kernel_size=4, padding=1),
            nn.Tanh(),
        )

        self.apply(weights_init_normal)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Encoder forward pass
        d1 = self.down1(x)
        d2 = self.down2(d1)
        d3 = self.down3(d2)
        d4 = self.down4(d3)
        d5 = self.down5(d4)
        d6 = self.down6(d5)
        d7 = self.down7(d6)
        d8 = self.down8(d7)

        # Decoder forward pass with concatenated skip connections
        u1 = self.up1(d8, d7)
        u2 = self.up2(u1, d6)
        u3 = self.up3(u2, d5)
        u4 = self.up4(u3, d4)
        u5 = self.up5(u4, d3)
        u6 = self.up6(u5, d2)
        u7 = self.up7(u6, d1)

        return self.final(u7)
