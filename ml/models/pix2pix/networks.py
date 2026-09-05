"""
Core Neural Network Building Blocks for pix2pix Architecture.
Includes encoder downsampling blocks, decoder upsampling blocks with skip connections,
and canonical Gaussian weight initialization.
"""

import torch
import torch.nn as nn


def weights_init_normal(m: nn.Module) -> None:
    """
    Initializes network weights from a normal distribution N(0, 0.02)
    and batch normalization weights N(1.0, 0.02), per the original pix2pix paper.
    """
    classname = m.__class__.__name__
    if classname.find("Conv") != -1:
        nn.init.normal_(m.weight.data, 0.0, 0.02)
        if hasattr(m, "bias") and m.bias is not None:
            nn.init.constant_(m.bias.data, 0.0)
    elif classname.find("BatchNorm2d") != -1:
        nn.init.normal_(m.weight.data, 1.0, 0.02)
        nn.init.constant_(m.bias.data, 0.0)


class UNetDown(nn.Module):
    """
    Encoder Downsampling Block:
    Conv2d (stride=2) -> [BatchNorm2d] -> LeakyReLU(0.2)
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        normalize: bool = True,
        dropout: float = 0.0,
    ):
        super().__init__()
        layers = [
            nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=4,
                stride=2,
                padding=1,
                bias=not normalize,
            )
        ]
        if normalize:
            layers.append(nn.BatchNorm2d(out_channels))
        layers.append(nn.LeakyReLU(0.2, inplace=True))
        if dropout > 0.0:
            layers.append(nn.Dropout(dropout))
        self.block = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class UNetUp(nn.Module):
    """
    Decoder Upsampling Block:
    ConvTranspose2d (stride=2) -> BatchNorm2d -> [Dropout] -> ReLU
    Concatenates skip connection from the corresponding encoder stage.
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        dropout: float = 0.0,
    ):
        super().__init__()
        layers = [
            nn.ConvTranspose2d(
                in_channels,
                out_channels,
                kernel_size=4,
                stride=2,
                padding=1,
                bias=False,
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        ]
        if dropout > 0.0:
            layers.append(nn.Dropout(dropout))
        self.block = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor, skip_input: torch.Tensor) -> torch.Tensor:
        x = self.block(x)
        return torch.cat([x, skip_input], dim=1)
