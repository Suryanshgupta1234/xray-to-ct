"""
Base Interface for Image-to-Image Medical Translation Models.
Allows seamless addition of CycleGAN, Diffusion Models, or U-Net direct translation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import torch
import torch.nn as nn


class BaseTranslationModel(nn.Module, ABC):
    """
    Abstract interface for medical image-to-image translation architectures.
    Decouples model execution from backend APIs and training loops.
    """

    def __init__(self, in_channels: int = 1, out_channels: int = 1):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass for inference: generates target translation from source."""
        pass

    @abstractmethod
    def get_generator(self) -> nn.Module:
        """Returns the generative network."""
        pass

    @abstractmethod
    def get_discriminator(self) -> Optional[nn.Module]:
        """Returns the discriminative network if adversarial, else None."""
        pass

    @abstractmethod
    def get_model_metadata(self) -> Dict[str, Any]:
        """Returns architectural parameters and metadata."""
        pass
