"""
Synthetic Mock Dataset Generator for Pipeline Verification.

IMPORTANT NOTE:
This script generates strictly SYNTHETIC, mathematical geometric phantom pairs
(simulated thoracic ellipses, rib silhouettes, and axial slice profiles) to verify
the software pipeline, PyTorch data loaders, training loops, and API endpoints.

IT DOES NOT CONTAIN OR FABRICATE REAL PATIENT MEDICAL DATA.
Every generated file is stamped with synthetic research watermarks.
"""

import os
import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def create_synthetic_thoracic_phantom(
    case_idx: int,
    size: int = 256,
    rng: np.random.Generator = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Synthesizes a paired 2D simulated X-ray (projection) and CT (cross-sectional slice)
    using procedural geometric primitives.

    Returns:
        tuple[np.ndarray, np.ndarray]: (synthetic_xray, synthetic_ct) in uint8 [0, 255]
    """
    if rng is None:
        rng = np.random.default_rng(case_idx)

    # 1. Base arrays
    xray = np.zeros((size, size), dtype=np.float32)
    ct = np.zeros((size, size), dtype=np.float32)

    # Coordinate grids centered at 0
    y, x = np.ogrid[:size, :size]
    cy, cx = size / 2.0, size / 2.0

    # Perturbations per case
    w_scale = 1.0 + rng.uniform(-0.08, 0.08)
    h_scale = 1.0 + rng.uniform(-0.08, 0.08)

    # --- Simulated Thoracic Cross-Section (CT Axial Slice) ---
    # Body contour (soft tissue HU ~ 40)
    body_mask = (((x - cx) / (100.0 * w_scale)) ** 2 + ((y - cy) / (85.0 * h_scale)) ** 2) <= 1.0
    ct[body_mask] = 100.0

    # Spine (high attenuation bone ~ 400 HU)
    spine_mask = (((x - cx) / 14.0) ** 2 + ((y - (cy + 60.0 * h_scale)) / 12.0) ** 2) <= 1.0
    ct[spine_mask] = 230.0

    # Rib cage (outer bony rim)
    rib_ring = (((x - cx) / (96.0 * w_scale)) ** 2 + ((y - cy) / (81.0 * h_scale)) ** 2) <= 1.0
    rib_inner = (((x - cx) / (88.0 * w_scale)) ** 2 + ((y - cy) / (73.0 * h_scale)) ** 2) <= 1.0
    ct[rib_ring & (~rib_inner)] = 210.0

    # Lungs (low attenuation air ~ -600 to -800 HU)
    left_lung = (((x - (cx - 45.0 * w_scale)) / 30.0) ** 2 + ((y - (cy - 10.0 * h_scale)) / 45.0) ** 2) <= 1.0
    right_lung = (((x - (cx + 45.0 * w_scale)) / 30.0) ** 2 + ((y - (cy - 10.0 * h_scale)) / 45.0) ** 2) <= 1.0
    ct[left_lung | right_lung] = 25.0

    # Mediastinum / Heart contour in CT
    heart = (((x - (cx - 15.0 * w_scale)) / 25.0) ** 2 + ((y - (cy + 10.0 * h_scale)) / 22.0) ** 2) <= 1.0
    ct[heart & (~spine_mask)] = 120.0

    # --- Simulated Planar Projection (X-ray Radiograph) ---
    # Thoracic cage silhouette
    thorax_proj = (((x - cx) / (95.0 * w_scale)) ** 2 + ((y - cy) / (105.0 * h_scale)) ** 2) <= 1.0
    xray[thorax_proj] = 70.0

    # Projected lung fields (radiolucent -> darker / lower attenuation)
    lung_proj_l = (((x - (cx - 45.0 * w_scale)) / 32.0) ** 2 + ((y - (cy - 20.0 * h_scale)) / 65.0) ** 2) <= 1.0
    lung_proj_r = (((x - (cx + 45.0 * w_scale)) / 32.0) ** 2 + ((y - (cy - 20.0 * h_scale)) / 65.0) ** 2) <= 1.0
    xray[lung_proj_l | lung_proj_r] = 20.0

    # Projected rib shadows (horizontal curved attenuation bands)
    for rib_y in range(int(cy - 60), int(cy + 60), 22):
        r_band = np.abs(y - rib_y - 0.05 * (x - cx) ** 2) < 3.5
        xray[r_band & thorax_proj] += 40.0

    # Projected spine column
    spine_proj = (np.abs(x - cx) < 12.0) & thorax_proj
    xray[spine_proj] += 80.0

    # Projected cardiac silhouette
    cardiac_proj = (((x - (cx - 20.0 * w_scale)) / 35.0) ** 2 + ((y - (cy + 25.0 * h_scale)) / 35.0) ** 2) <= 1.0
    xray[cardiac_proj] += 90.0

    # Add realistic gentle Poisson/Gaussian noise
    noise_xray = rng.normal(0, 3.0, (size, size))
    noise_ct = rng.normal(0, 3.0, (size, size))
    xray = np.clip(xray + noise_xray, 0, 255).astype(np.uint8)
    ct = np.clip(ct + noise_ct, 0, 255).astype(np.uint8)

    return xray, ct


def watermark_mock_image(img_arr: np.ndarray, label: str) -> Image.Image:
    """Burn in research mock label to ensure data can never be mistaken for real patient imaging."""
    img = Image.fromarray(img_arr, mode="L")
    draw = ImageDraw.Draw(img)
    # Small top notice
    draw.text((6, 6), f"SYNTHETIC MOCK ({label})", fill=255)
    draw.text((6, img.height - 16), "NON-CLINICAL PHANTOM", fill=200)
    return img


def generate_mock_dataset(
    output_dir: Path,
    num_train: int = 24,
    num_val: int = 6,
    num_test: int = 6,
    seed: int = 42,
) -> None:
    """
    Generates a mock paired dataset split into train/val/test partitions.
    """
    output_dir = Path(output_dir)
    splits = {
        "train": num_train,
        "val": num_val,
        "test": num_test,
    }

    rng = np.random.default_rng(seed)
    total_generated = 0

    print(f"Generating synthetic mock paired dataset in '{output_dir}' (Seed: {seed})...")

    for split_name, count in splits.items():
        xray_dir = output_dir / split_name / "xray"
        ct_dir = output_dir / split_name / "ct"
        xray_dir.mkdir(parents=True, exist_ok=True)
        ct_dir.mkdir(parents=True, exist_ok=True)

        for i in range(count):
            case_id = f"phantom_{split_name}_{i+1:03d}"
            xray_np, ct_np = create_synthetic_thoracic_phantom(
                case_idx=total_generated, size=256, rng=rng
            )

            xray_img = watermark_mock_image(xray_np, f"{case_id}_XRAY")
            ct_img = watermark_mock_image(ct_np, f"{case_id}_CT")

            xray_path = xray_dir / f"{case_id}.png"
            ct_path = ct_dir / f"{case_id}.png"

            xray_img.save(xray_path, format="PNG")
            ct_img.save(ct_path, format="PNG")

            total_generated += 1

        print(f"  [OK] [{split_name}] Created {count} paired samples in {split_name}/xray and {split_name}/ct")

    # Generate metadata manifest
    manifest_path = output_dir / "MOCK_DATASET_MANIFEST.json"
    import json
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "is_synthetic_mock": True,
            "disclaimer": "SYNTHETIC PHANTOM DATA STRICTLY FOR PIPELINE TESTING. NOT REAL CLINICAL DATA.",
            "total_pairs": total_generated,
            "splits": splits,
            "resolution": [256, 256],
            "seed": seed,
        }, f, indent=2)

    print(f"Dataset generation complete. Total pairs: {total_generated}. Manifest: {manifest_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic mock paired X-ray/CT dataset")
    parser.add_argument("--output_dir", type=str, default="./datasets", help="Root datasets directory")
    parser.add_argument("--train", type=int, default=24, help="Number of train pairs")
    parser.add_argument("--val", type=int, default=6, help="Number of val pairs")
    parser.add_argument("--test", type=int, default=6, help="Number of test pairs")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed")

    args = parser.parse_args()
    generate_mock_dataset(
        output_dir=Path(args.output_dir),
        num_train=args.train,
        num_val=args.val,
        num_test=args.test,
        seed=args.seed,
    )
