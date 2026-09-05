"""
Loss Functions for pix2pix Conditional GAN Translation.
Implements PatchGAN Adversarial Loss and L1 Pixel Reconstruction Loss with configurable lambda.
"""

import torch
import torch.nn as nn
from typing import Tuple


class Pix2PixLosses(nn.Module):
    """
    Composite loss calculation for pix2pix.
    Total Generator Loss = L_GAN(D(x, G(x)), 1) + lambda_l1 * L1(y, G(x))
    Total Discriminator Loss = 0.5 * (L_GAN(D(x, y), 1) + L_GAN(D(x, G(x)), 0))
    """

    def __init__(self, lambda_l1: float = 100.0, use_lsgan: bool = True):
        super().__init__()
        self.lambda_l1 = lambda_l1
        # LSGAN (Least Squares GAN via MSE) provides smoother gradients and mitigates vanishing gradients
        self.criterion_gan = nn.MSELoss() if use_lsgan else nn.BCEWithLogitsLoss()
        self.criterion_l1 = nn.L1Loss()

    def generator_loss(
        self,
        d_fake_logits: torch.Tensor,
        fake_images: torch.Tensor,
        real_images: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Calculates generator composite loss.

        Returns:
            Tuple[total_g_loss, g_gan_loss, g_l1_loss]
        """
        target_real = torch.ones_like(d_fake_logits)
        loss_gan = self.criterion_gan(d_fake_logits, target_real)
        loss_l1 = self.criterion_l1(fake_images, real_images)
        loss_total = loss_gan + (self.lambda_l1 * loss_l1)
        return loss_total, loss_gan, loss_l1

    def discriminator_loss(
        self,
        d_real_logits: torch.Tensor,
        d_fake_logits: torch.Tensor,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Calculates discriminator composite loss.

        Returns:
            Tuple[total_d_loss, d_real_loss, d_fake_loss]
        """
        target_real = torch.ones_like(d_real_logits)
        target_fake = torch.zeros_like(d_fake_logits)

        loss_real = self.criterion_gan(d_real_logits, target_real)
        loss_fake = self.criterion_gan(d_fake_logits, target_fake)
        loss_total = 0.5 * (loss_real + loss_fake)
        return loss_total, loss_real, loss_fake
