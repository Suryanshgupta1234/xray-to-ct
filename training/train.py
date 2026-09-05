"""
Main Training Script for pix2pix X-Ray to CT Translation.
Usage:
    python training/train.py --config training/config.yaml
"""

import sys
import argparse
import json
import yaml
from pathlib import Path
import torch
from torch.utils.data import DataLoader

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datasets.dataset import PairedXrayCTDataset
from training.trainer import Pix2PixTrainer


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="Train pix2pix X-Ray to CT translation model")
    parser.add_argument("--config", type=str, default="training/config.yaml", help="Path to config YAML")
    parser.add_argument("--epochs", type=int, default=None, help="Override number of epochs")
    parser.add_argument("--batch_size", type=int, default=None, help="Override batch size")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.epochs:
        config["hyperparameters"]["num_epochs"] = args.epochs
    if args.batch_size:
        config["hyperparameters"]["batch_size"] = args.batch_size

    ds_cfg = config.get("dataset", {})
    hp = config.get("hyperparameters", {})
    sys_cfg = config.get("system", {})
    model_cfg = config.get("model", {})

    root_dir = Path(ds_cfg.get("root_dir", "./datasets"))
    train_dir = root_dir / ds_cfg.get("train_split", "train")
    val_dir = root_dir / ds_cfg.get("val_split", "val")

    print("\n=======================================================")
    print(" Starting pix2pix X-Ray -> CT Translation Training")
    print("=======================================================")
    print(f"Model: {model_cfg.get('name')} (Version: {model_cfg.get('version')})")
    print(f"Batch Size: {hp.get('batch_size')}, Epochs: {hp.get('num_epochs')}")
    print(f"L1 Loss Weight (lambda): {hp.get('lambda_l1')}")

    # Initialize Datasets
    train_dataset = PairedXrayCTDataset(
        split_dir=train_dir,
        image_size=tuple(model_cfg.get("image_size", [256, 256])),
        in_channels=model_cfg.get("in_channels", 1),
        out_channels=model_cfg.get("out_channels", 1),
        augment=ds_cfg.get("augment", True),
    )

    val_dataset = PairedXrayCTDataset(
        split_dir=val_dir,
        image_size=tuple(model_cfg.get("image_size", [256, 256])),
        in_channels=model_cfg.get("in_channels", 1),
        out_channels=model_cfg.get("out_channels", 1),
        augment=False,
    )

    if len(train_dataset) == 0:
        print(f"\n[Error] No paired samples found in {train_dir}.")
        print("Please generate mock data first using:")
        print("    python datasets/sample_generator.py")
        sys.exit(1)

    print(f"Dataset Loaded: {len(train_dataset)} train pairs, {len(val_dataset)} val pairs.")

    train_loader = DataLoader(
        train_dataset,
        batch_size=hp.get("batch_size", 4),
        shuffle=True,
        num_workers=sys_cfg.get("num_workers", 0),
        pin_memory=torch.cuda.is_available(),
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=hp.get("batch_size", 4),
        shuffle=False,
        num_workers=sys_cfg.get("num_workers", 0),
    )

    # Initialize Trainer
    trainer = Pix2PixTrainer(config)

    num_epochs = hp.get("num_epochs", 30)
    best_ssim = -1.0
    best_metrics = {}

    for epoch in range(1, num_epochs + 1):
        train_stats = trainer.train_epoch(train_loader, epoch)
        val_stats = trainer.validate(val_loader)

        ssim = val_stats["SSIM"]
        is_best = ssim > best_ssim
        if is_best:
            best_ssim = ssim
            best_metrics = val_stats

        print(
            f"Epoch [{epoch:02d}/{num_epochs:02d}] "
            f"Loss G: {train_stats['loss_g']:.4f} | "
            f"Loss D: {train_stats['loss_d']:.4f} | "
            f"Val SSIM: {val_stats['SSIM']:.4f} | "
            f"Val PSNR: {val_stats['PSNR_dB']:.2f}dB"
            f"{' (* Best)' if is_best else ''}"
        )

        # Periodic checkpoint
        if epoch % sys_cfg.get("checkpoint_frequency_epochs", 5) == 0 or is_best:
            trainer.save_checkpoint(epoch, val_stats, is_best=is_best)

    # Export production model to models/v1
    prod_model_dir = Path("./models") / model_cfg.get("version", "v1")
    prod_model_dir.mkdir(parents=True, exist_ok=True)
    prod_weights_path = prod_model_dir / "generator.pth"
    torch.save(trainer.generator.state_dict(), prod_weights_path)

    # Export Model Metadata Manifest
    metadata_path = prod_model_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump({
            "model_name": model_cfg.get("name"),
            "version": model_cfg.get("version"),
            "architecture": "pix2pix_UNet256_PatchGAN",
            "image_size": model_cfg.get("image_size"),
            "in_channels": model_cfg.get("in_channels"),
            "out_channels": model_cfg.get("out_channels"),
            "hyperparameters": hp,
            "best_validation_metrics": best_metrics,
            "disclaimer": "AI-generated research model weights. NOT FOR CLINICAL DIAGNOSIS.",
        }, f, indent=2)

    print(f"\n[SUCCESS] Training Complete!")
    print(f"Production generator saved to: {prod_weights_path}")
    print(f"Model metadata manifest saved to: {metadata_path}")


if __name__ == "__main__":
    main()
