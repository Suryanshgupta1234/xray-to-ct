"""
Model Registry & In-Memory Cache.
Provides singleton model caching, GPU/CPU hardware detection, and warm-up cycles.
Eliminates disk reloads across consecutive user inference requests.
"""

import threading
from pathlib import Path
from typing import Dict, Any, Optional
import torch

from app.core.config import settings
from app.core.logging import logger
from app.ml.model_loader import load_generator_weights
from ml.models.pix2pix.generator import UNetGenerator


class ModelRegistry:
    """Thread-safe in-memory cache for machine learning translation models."""

    _instance: Optional["ModelRegistry"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self._models: Dict[str, UNetGenerator] = {}
        self._device = self._determine_device()
        self._initialized = True
        logger.info(f"ModelRegistry initialized on device: {self._device}")

    def _determine_device(self) -> torch.device:
        req = settings.DEVICE.lower()
        if req == "cuda" and torch.cuda.is_available():
            return torch.device("cuda")
        elif req == "auto":
            return torch.device("cuda" if torch.cuda.is_available() else "cpu")
        return torch.device("cpu")

    @property
    def device(self) -> torch.device:
        return self._device

    def get_model(self, version: Optional[str] = None) -> UNetGenerator:
        """Retrieves cached model or loads and caches it on first request."""
        ver = version or settings.ACTIVE_MODEL_VERSION

        if ver in self._models:
            return self._models[ver]

        with self._lock:
            if ver in self._models:
                return self._models[ver]

            # Robust search across candidate model directories
            candidates = [
                Path(settings.MODEL_DIR) / ver / "generator.pth",
                Path("./models") / ver / "generator.pth",
                Path("../models") / ver / "generator.pth",
                Path(settings.ACTIVE_MODEL_PATH),
            ]
            weights_file = candidates[0]
            for c in candidates:
                if c.exists():
                    weights_file = c
                    break

            logger.info(f"Loading model version '{ver}' from {weights_file.resolve()}")
            model = load_generator_weights(str(weights_file), device=self._device)

            # Warm-up inference
            self._warmup(model)

            self._models[ver] = model
            return model

    def _warmup(self, model: UNetGenerator) -> None:
        """Runs a zero-tensor dummy forward pass to warm up PyTorch CUDA kernels."""
        try:
            with torch.inference_mode():
                dummy = torch.zeros(1, 1, 256, 256, device=self._device)
                _ = model(dummy)
            logger.info("Model warm-up completed successfully.")
        except Exception as e:
            logger.warning(f"Model warm-up encountered warning: {e}")

    def check_health(self) -> Dict[str, Any]:
        return {
            "cached_versions": list(self._models.keys()),
            "active_version": settings.ACTIVE_MODEL_VERSION,
            "device": str(self._device),
            "cuda_available": torch.cuda.is_available(),
        }


model_registry = ModelRegistry()
