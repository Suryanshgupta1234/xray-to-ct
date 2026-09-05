"""
Runtime Predictor Module.
Executes forward-pass inference in torch.inference_mode() with millisecond latency timing.
"""

import time
from typing import Tuple, Optional
import torch

from app.ml.model_registry import model_registry
from app.core.logging import logger


class Predictor:
    """Stateless inference runner using cached model weights."""

    def __init__(self, model_version: Optional[str] = None):
        self.model_version = model_version
        self.registry = model_registry

    def predict(self, input_tensor: torch.Tensor) -> Tuple[torch.Tensor, float]:
        """
        Executes model forward pass.

        Args:
            input_tensor: Tensor of shape (1, 1, H, W) normalized to [-1.0, 1.0].

        Returns:
            Tuple[torch.Tensor, float]: (output_tensor in [-1.0, 1.0], execution_time_ms)
        """
        model = self.registry.get_model(self.model_version)
        device = self.registry.device

        tensor_on_dev = input_tensor.to(device)

        start_time = time.perf_counter()
        with torch.inference_mode():
            output_tensor = model(tensor_on_dev)
        end_time = time.perf_counter()

        latency_ms = (end_time - start_time) * 1000.0

        return output_tensor.cpu(), latency_ms
