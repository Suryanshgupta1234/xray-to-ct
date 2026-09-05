"""
Trainer Engine for pix2pix Image-to-Image Translation.
Handles GPU/CPU device detection, alternating GAN optimization steps,
validation evaluations, metric tracking, and model checkpointing.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import LambdaLR

from ml.models.pix2pix import Pix2PixModel
from training.losses import Pix2PixLosses
from training.metrics import evaluate_batch


class Pix2PixTrainer:
    """Orchestrates end-to-end training of the pix2pix translation system."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.hp = config.get("hyperparameters", {})
        self.sys_cfg = config.get("system", {})
        self.model_cfg = config.get("model", {})

        # 1. Device selection
        req_dev = self.sys_cfg.get("device", "auto")
        if req_dev == "cuda" and torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif req_dev == "auto":
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device("cpu")

        print(f"[Trainer] Running on device: {self.device} (CUDA Available: {torch.cuda.is_available()})")

        # 2. Model Initialization
        self.model = Pix2PixModel(
            in_channels=self.model_cfg.get("in_channels", 1),
            out_channels=self.model_cfg.get("out_channels", 1),
        ).to(self.device)

        self.generator = self.model.get_generator()
        self.discriminator = self.model.get_discriminator()

        # 3. Losses
        self.criterion = Pix2PixLosses(
            lambda_l1=self.hp.get("lambda_l1", 100.0),
            use_lsgan=self.hp.get("use_lsgan", True),
        ).to(self.device)

        # 4. Optimizers
        lr_g = self.hp.get("lr_generator", 0.0002)
        lr_d = self.hp.get("lr_discriminator", 0.0002)
        b1 = self.hp.get("beta1", 0.5)
        b2 = self.hp.get("beta2", 0.999)

        self.optimizer_g = torch.optim.Adam(self.generator.parameters(), lr=lr_g, betas=(b1, b2))
        self.optimizer_d = torch.optim.Adam(self.discriminator.parameters(), lr=lr_d, betas=(b1, b2))

        # 5. Learning rate decay scheduler
        num_epochs = self.hp.get("num_epochs", 30)
        decay_start = self.hp.get("lr_decay_start_epoch", 15)

        def lr_lambda(epoch: int) -> float:
            if epoch < decay_start:
                return 1.0
            return 1.0 - (epoch - decay_start) / max(1, num_epochs - decay_start)

        self.scheduler_g = LambdaLR(self.optimizer_g, lr_lambda=lr_lambda)
        self.scheduler_d = LambdaLR(self.optimizer_d, lr_lambda=lr_lambda)

        # 6. Tracking
        self.checkpoint_dir = Path(self.sys_cfg.get("checkpoint_dir", "./training/checkpoints"))
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.best_val_loss = float("inf")
        self.best_ssim = -1.0
        self.patience_counter = 0

    def train_epoch(self, dataloader: DataLoader, epoch: int) -> Dict[str, float]:
        """Trains one complete epoch across the dataset."""
        self.generator.train()
        self.discriminator.train()

        running_g_loss = 0.0
        running_d_loss = 0.0
        running_l1_loss = 0.0
        num_batches = len(dataloader)

        for batch_idx, batch in enumerate(dataloader):
            real_x = batch["xray"].to(self.device)
            real_y = batch["ct"].to(self.device)

            # ----------------------------------------------------
            # 1. Train Discriminator
            # ----------------------------------------------------
            self.optimizer_d.zero_grad()

            # Real CT evaluation
            d_real_logits = self.discriminator(real_x, real_y)

            # Fake CT evaluation (detached so gradients don't flow back to G)
            with torch.no_grad():
                fake_y = self.generator(real_x)
            d_fake_logits = self.discriminator(real_x, fake_y.detach())

            loss_d, _, _ = self.criterion.discriminator_loss(d_real_logits, d_fake_logits)
            loss_d.backward()
            self.optimizer_d.step()

            # ----------------------------------------------------
            # 2. Train Generator
            # ----------------------------------------------------
            self.optimizer_g.zero_grad()

            # Synthesize fresh fake CT for generator gradients
            fake_y = self.generator(real_x)
            d_fake_logits_for_g = self.discriminator(real_x, fake_y)

            loss_g, loss_gan, loss_l1 = self.criterion.generator_loss(
                d_fake_logits_for_g, fake_y, real_y
            )
            loss_g.backward()
            self.optimizer_g.step()

            running_g_loss += loss_g.item()
            running_d_loss += loss_d.item()
            running_l1_loss += loss_l1.item()

        self.scheduler_g.step()
        self.scheduler_d.step()

        return {
            "loss_g": running_g_loss / max(1, num_batches),
            "loss_d": running_d_loss / max(1, num_batches),
            "loss_l1": running_l1_loss / max(1, num_batches),
        }

    @torch.no_grad()
    def validate(self, dataloader: DataLoader) -> Dict[str, float]:
        """Runs validation pass without gradient tracking."""
        self.generator.eval()
        self.discriminator.eval()

        total_loss = 0.0
        all_mae, all_mse, all_psnr, all_ssim = [], [], [], []
        num_batches = len(dataloader)

        if num_batches == 0:
            return {"val_loss": 0.0, "MAE": 0.0, "MSE": 0.0, "PSNR_dB": 0.0, "SSIM": 0.0}

        for batch in dataloader:
            real_x = batch["xray"].to(self.device)
            real_y = batch["ct"].to(self.device)

            fake_y = self.generator(real_x)
            d_fake_logits = self.discriminator(real_x, fake_y)

            loss_g, _, _ = self.criterion.generator_loss(d_fake_logits, fake_y, real_y)
            total_loss += loss_g.item()

            metrics = evaluate_batch(fake_y, real_y)
            all_mae.append(metrics["MAE"])
            all_mse.append(metrics["MSE"])
            all_psnr.append(metrics["PSNR_dB"])
            all_ssim.append(metrics["SSIM"])

        return {
            "val_loss": round(total_loss / num_batches, 4),
            "MAE": round(sum(all_mae) / len(all_mae), 6),
            "MSE": round(sum(all_mse) / len(all_mse), 6),
            "PSNR_dB": round(sum(all_psnr) / len(all_psnr), 2),
            "SSIM": round(sum(all_ssim) / len(all_ssim), 4),
        }

    def save_checkpoint(
        self,
        epoch: int,
        metrics: Dict[str, float],
        is_best: bool = False,
    ) -> Path:
        """Saves weights and training state manifest."""
        checkpoint_path = self.checkpoint_dir / f"checkpoint_epoch_{epoch:03d}.pth"
        payload = {
            "epoch": epoch,
            "generator_state_dict": self.generator.state_dict(),
            "discriminator_state_dict": self.discriminator.state_dict(),
            "optimizer_g_state_dict": self.optimizer_g.state_dict(),
            "optimizer_d_state_dict": self.optimizer_d.state_dict(),
            "metrics": metrics,
            "config": self.config,
        }
        torch.save(payload, checkpoint_path)

        if is_best:
            best_path = self.checkpoint_dir / "best_generator.pth"
            # Also save raw generator state for clean production inference
            torch.save(self.generator.state_dict(), best_path)

        return checkpoint_path
