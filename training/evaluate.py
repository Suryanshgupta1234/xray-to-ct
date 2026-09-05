"""
Offline Model Evaluation and Visual Comparison Generator.
Evaluates model fidelity on the test split (MAE, MSE, PSNR, SSIM)
and exports side-by-side qualitative comparison grids.
"""

import sys
import argparse
import json
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from datasets.dataset import PairedXrayCTDataset
from ml.models.pix2pix.generator import UNetGenerator
from ml.preprocessing.transforms import tensor_to_pil
from training.metrics import calculate_mae, calculate_mse, calculate_psnr, calculate_ssim


def create_comparison_grid(
    xray_img: Image.Image,
    real_ct: Image.Image,
    fake_ct: Image.Image,
) -> Image.Image:
    """Combines X-ray, Real CT, Synthesized CT, and Error Map into a 4-panel visual strip."""
    w, h = xray_img.size
    grid = Image.new("RGB", (w * 4, h + 30), color=(20, 24, 33))

    # Error map (Absolute difference)
    arr_real = np.array(real_ct, dtype=np.float32)
    arr_fake = np.array(fake_ct, dtype=np.float32)
    diff = np.abs(arr_real - arr_fake)
    # Scale difference map for visualization
    diff_norm = np.clip((diff / 128.0) * 255.0, 0, 255).astype(np.uint8)
    diff_img = Image.fromarray(diff_norm, mode="L").convert("RGB")

    # Paste panels
    grid.paste(xray_img.convert("RGB"), (0, 30))
    grid.paste(real_ct.convert("RGB"), (w, 30))
    grid.paste(fake_ct.convert("RGB"), (w * 2, 30))
    grid.paste(diff_img, (w * 3, 30))

    from PIL import ImageDraw
    draw = ImageDraw.Draw(grid)
    draw.text((10, 8), "Input X-Ray", fill=(200, 210, 225))
    draw.text((w + 10, 8), "Target CT (Ground Truth)", fill=(200, 210, 225))
    draw.text((w * 2 + 10, 8), "Synthesized CT (AI Generated)", fill=(100, 220, 150))
    draw.text((w * 3 + 10, 8), "Error Map (|Real - Fake|)", fill=(255, 120, 120))

    return grid


def run_evaluation(
    model_path: str,
    dataset_dir: str,
    output_dir: str = "./results/evaluation",
    device: str = "auto",
):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if device == "auto":
        dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        dev = torch.device(device)

    print(f"\n=======================================================")
    print(f" Evaluating pix2pix Translation on Test Partition")
    print(f" Device: {dev} | Checkpoint: {model_path}")
    print(f"=======================================================\n")

    # Load generator
    generator = UNetGenerator(in_channels=1, out_channels=1).to(dev)
    state = torch.load(model_path, map_location=dev)
    if "generator_state_dict" in state:
        generator.load_state_dict(state["generator_state_dict"])
    else:
        generator.load_state_dict(state)
    generator.eval()

    # Load test dataset
    test_ds = PairedXrayCTDataset(
        split_dir=Path(dataset_dir) / "test",
        image_size=(256, 256),
        in_channels=1,
        out_channels=1,
        augment=False,
    )

    if len(test_ds) == 0:
        print(f"[Warning] Test dataset is empty in {dataset_dir}/test.")
        return

    test_loader = DataLoader(test_ds, batch_size=1, shuffle=False)

    all_mae, all_mse, all_psnr, all_ssim = [], [], [], []
    per_case_metrics = []

    with torch.no_grad():
        for idx, batch in enumerate(test_loader):
            case_id = batch["id"][0]
            real_x = batch["xray"].to(dev)
            real_y = batch["ct"].to(dev)

            fake_y = generator(real_x)

            mae = calculate_mae(fake_y, real_y)
            mse = calculate_mse(fake_y, real_y)
            psnr = calculate_psnr(fake_y, real_y)
            ssim = calculate_ssim(fake_y, real_y)

            all_mae.append(mae)
            all_mse.append(mse)
            all_psnr.append(psnr)
            all_ssim.append(ssim)

            per_case_metrics.append({
                "case_id": case_id,
                "MAE": round(mae, 6),
                "MSE": round(mse, 6),
                "PSNR_dB": round(psnr, 2),
                "SSIM": round(ssim, 4),
            })

            # Save qualitative visual grid
            pil_x = tensor_to_pil(real_x[0])
            pil_real = tensor_to_pil(real_y[0])
            pil_fake = tensor_to_pil(fake_y[0])

            grid = create_comparison_grid(pil_x, pil_real, pil_fake)
            grid.save(out_path / f"eval_comparison_{case_id}.png")

    avg_mae = float(np.mean(all_mae))
    avg_mse = float(np.mean(all_mse))
    avg_psnr = float(np.mean(all_psnr))
    avg_ssim = float(np.mean(all_ssim))

    report = {
        "summary": {
            "total_test_samples": len(test_ds),
            "mean_MAE": round(avg_mae, 6),
            "mean_MSE": round(avg_mse, 6),
            "mean_PSNR_dB": round(avg_psnr, 2),
            "mean_SSIM": round(avg_ssim, 4),
        },
        "per_case_results": per_case_metrics,
        "disclaimer": (
            "Mathematical signal metrics (MAE, MSE, PSNR, SSIM) evaluate pixel-level and "
            "structural correlation between synthetic representations and ground truth. "
            "THEY DO NOT ESTABLISH CLINICAL SAFETY, ANATOMICAL VALIDITY, OR DIAGNOSTIC ACCURACY. "
            "AI-generated CT-like representations must not be used for diagnostic medical decisions."
        ),
    }

    report_path = out_path / "evaluation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("--- Test Evaluation Summary ---")
    print(f"Total Test Cases: {len(test_ds)}")
    print(f"Mean SSIM:       {avg_ssim:.4f}")
    print(f"Mean PSNR:       {avg_psnr:.2f} dB")
    print(f"Mean MAE:        {avg_mae:.6f}")
    print(f"Mean MSE:        {avg_mse:.6f}")
    print(f"Visual Grids:    {out_path}/eval_comparison_*.png")
    print(f"Full Report:     {report_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate pix2pix model on test set")
    parser.add_argument("--model", type=str, default="./models/v1/generator.pth", help="Path to generator weights")
    parser.add_argument("--dataset", type=str, default="./datasets", help="Root dataset directory")
    parser.add_argument("--output", type=str, default="./results/evaluation", help="Output directory")
    args = parser.parse_args()

    run_evaluation(model_path=args.model, dataset_dir=args.dataset, output_dir=args.output)
