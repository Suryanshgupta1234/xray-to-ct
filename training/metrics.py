"""
Model Evaluation Metrics for Image-to-Image Medical Translation.
Calculates MAE, MSE, PSNR, and SSIM.
Includes clear medical documentation that numerical metrics do NOT establish clinical diagnostic validity.
"""

import math
from typing import Dict
import numpy as np
import torch
import torch.nn.functional as F


def calculate_mae(pred: torch.Tensor, target: torch.Tensor) -> float:
    """Mean Absolute Error (L1 norm)."""
    return torch.mean(torch.abs(pred - target)).item()


def calculate_mse(pred: torch.Tensor, target: torch.Tensor) -> float:
    """Mean Squared Error (L2 norm)."""
    return torch.mean((pred - target) ** 2).item()


def calculate_psnr(
    pred: torch.Tensor,
    target: torch.Tensor,
    data_range: float = 2.0,
) -> float:
    """
    Peak Signal-to-Noise Ratio (PSNR) in decibels (dB).
    Default data_range is 2.0 for tensors normalized to [-1.0, 1.0].
    """
    mse = calculate_mse(pred, target)
    if mse <= 1e-10:
        return 100.0  # Perfect reconstruction ceiling
    return 10.0 * math.log10((data_range ** 2) / mse)


def _gaussian_kernel(window_size: int, sigma: float) -> torch.Tensor:
    coords = torch.arange(window_size).float() - window_size // 2
    g = torch.exp(-(coords ** 2) / (2 * sigma ** 2))
    g = g / g.sum()
    kernel_2d = g.unsqueeze(1) * g.unsqueeze(0)
    return kernel_2d.unsqueeze(0).unsqueeze(0)


def calculate_ssim(
    img1: torch.Tensor,
    img2: torch.Tensor,
    window_size: int = 11,
    sigma: float = 1.5,
    data_range: float = 2.0,
) -> float:
    """
    Structural Similarity Index (SSIM) computed via Gaussian convolution in PyTorch.
    Works directly on GPU or CPU tensors without CPU/NumPy conversion overhead.
    """
    if img1.ndim == 3:
        img1 = img1.unsqueeze(0)
    if img2.ndim == 3:
        img2 = img2.unsqueeze(0)

    channels = img1.shape[1]
    kernel = _gaussian_kernel(window_size, sigma).to(img1.device)
    kernel = kernel.repeat(channels, 1, 1, 1)

    c1 = (0.01 * data_range) ** 2
    c2 = (0.03 * data_range) ** 2

    mu1 = F.conv2d(img1, kernel, padding=window_size // 2, groups=channels)
    mu2 = F.conv2d(img2, kernel, padding=window_size // 2, groups=channels)

    mu1_sq = mu1.pow(2)
    mu2_sq = mu2.pow(2)
    mu1_mu2 = mu1 * mu2

    sigma1_sq = F.conv2d(img1 * img1, kernel, padding=window_size // 2, groups=channels) - mu1_sq
    sigma2_sq = F.conv2d(img2 * img2, kernel, padding=window_size // 2, groups=channels) - mu2_sq
    sigma12 = F.conv2d(img1 * img2, kernel, padding=window_size // 2, groups=channels) - mu1_mu2

    ssim_map = ((2 * mu1_mu2 + c1) * (2 * sigma12 + c2)) / (
        (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2)
    )
    return ssim_map.mean().item()


def evaluate_batch(
    predictions: torch.Tensor,
    targets: torch.Tensor,
    data_range: float = 2.0,
) -> Dict[str, float]:
    """
    Computes all standard fidelity metrics for a batch.

    Returns:
        Dict containing MAE, MSE, PSNR, and SSIM.
    """
    mae = calculate_mae(predictions, targets)
    mse = calculate_mse(predictions, targets)
    psnr = calculate_psnr(predictions, targets, data_range=data_range)
    ssim = calculate_ssim(predictions, targets, data_range=data_range)

    return {
        "MAE": round(mae, 6),
        "MSE": round(mse, 6),
        "PSNR_dB": round(psnr, 2),
        "SSIM": round(ssim, 4),
    }
