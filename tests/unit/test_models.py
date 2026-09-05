"""
Unit Tests for pix2pix Neural Network Architectures.
Verifies forward-pass tensor shapes, skip-connection stability, and loss calculations.
"""

import sys
from pathlib import Path
import pytest
import torch

# Ensure repository root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.models.pix2pix.generator import UNetGenerator
from ml.models.pix2pix.discriminator import PatchGANDiscriminator
from ml.models.pix2pix import Pix2PixModel
from training.losses import Pix2PixLosses
from training.metrics import calculate_mae, calculate_mse, calculate_psnr, calculate_ssim


def test_generator_forward_shape():
    """Generator must accept (B, 1, 256, 256) and return (B, 1, 256, 256) in [-1, 1]."""
    generator = UNetGenerator(in_channels=1, out_channels=1)
    generator.eval()

    dummy_input = torch.randn(2, 1, 256, 256)
    with torch.no_grad():
        output = generator(dummy_input)

    assert output.shape == (2, 1, 256, 256)
    # Output must be bounded strictly by Tanh [-1.0, 1.0]
    assert output.min().item() >= -1.01
    assert output.max().item() <= 1.01


def test_patchgan_discriminator_shape():
    """Discriminator must accept condition + target and return a 2D patch logit grid."""
    discriminator = PatchGANDiscriminator(in_channels=1, out_channels=1)
    discriminator.eval()

    condition = torch.randn(2, 1, 256, 256)
    target = torch.randn(2, 1, 256, 256)

    with torch.no_grad():
        patch_logits = discriminator(condition, target)

    # For 256x256 input, 70x70 PatchGAN yields a 30x30 patch grid
    assert patch_logits.shape == (2, 1, 30, 30)


def test_pix2pix_loss_computation():
    """Validates combined generator and discriminator loss calculations."""
    criterion = Pix2PixLosses(lambda_l1=100.0, use_lsgan=True)

    d_fake_logits = torch.randn(2, 1, 30, 30)
    fake_img = torch.randn(2, 1, 256, 256)
    real_img = torch.randn(2, 1, 256, 256)

    g_total, g_gan, g_l1 = criterion.generator_loss(d_fake_logits, fake_img, real_img)

    assert g_total.item() > 0
    assert g_l1.item() >= 0
    # g_total must equal g_gan + 100 * g_l1
    assert abs(g_total.item() - (g_gan.item() + 100.0 * g_l1.item())) < 1e-4

    d_real_logits = torch.randn(2, 1, 30, 30)
    d_total, _, _ = criterion.discriminator_loss(d_real_logits, d_fake_logits)
    assert d_total.item() > 0


def test_evaluation_metrics_deterministic():
    """Verifies that identical tensors return zero error and perfect SSIM/PSNR."""
    img = torch.rand(1, 1, 64, 64) * 2.0 - 1.0  # [-1, 1]

    mae = calculate_mae(img, img)
    mse = calculate_mse(img, img)
    psnr = calculate_psnr(img, img)
    ssim = calculate_ssim(img, img)

    assert mae == pytest.approx(0.0, abs=1e-6)
    assert mse == pytest.approx(0.0, abs=1e-6)
    assert psnr >= 90.0  # Near infinite decibels
    assert ssim == pytest.approx(1.0, abs=1e-3)
