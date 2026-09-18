"""
Clinical DRR and Multi-Slice CT Dataset Builder.
Populates datasets/train, datasets/val, and datasets/test with realistic
paired 2D Digitally Reconstructed Radiographs (DRRs) and axial CT slices.
"""

import os
import shutil
from pathlib import Path
from ml.preprocessing.drr_generator import (
    create_realistic_brain_ct_volume,
    create_realistic_chest_ct_volume,
    make_synthetic_xray,
    make_ct_slice,
)
import cv2


def build_splits(root_dir: str = "datasets", img_size: int = 256):
    root = Path(root_dir)
    splits = {
        "train": 24,
        "val": 6,
        "test": 6,
    }

    print("==================================================")
    print(" Building Clinical DRR -> CT Paired Dataset")
    print("==================================================")

    total_generated = 0
    case_idx = 1

    for split_name, count in splits.items():
        xray_dir = root / split_name / "xray"
        ct_dir = root / split_name / "ct"
        xray_dir.mkdir(parents=True, exist_ok=True)
        ct_dir.mkdir(parents=True, exist_ok=True)

        for i in range(count):
            # Alternating Brain CT vs Thoracic Chest CT
            is_brain = (case_idx % 2 == 1)
            if is_brain:
                vol = create_realistic_brain_ct_volume()
                xray = make_synthetic_xray(vol, projection_axis=2)
                ct = make_ct_slice(vol)
                modality = "brain"
            else:
                vol = create_realistic_chest_ct_volume()
                xray = make_synthetic_xray(vol, projection_axis=1)
                ct = make_ct_slice(vol)
                modality = "chest"

            xray_res = cv2.resize(xray, (img_size, img_size), interpolation=cv2.INTER_AREA)
            ct_res = cv2.resize(ct, (img_size, img_size), interpolation=cv2.INTER_AREA)

            fn = f"case_{case_idx:04d}_{modality}.png"
            cv2.imwrite(str(xray_dir / fn), xray_res)
            cv2.imwrite(str(ct_dir / fn), ct_res)

            case_idx += 1
            total_generated += 1

        print(f"  [OK] {split_name:5s} split populated with {count} realistic pairs ({xray_dir})")

    print("==================================================")
    print(f"Total clinical pairs synthesized: {total_generated}")
    print("==================================================")


if __name__ == "__main__":
    build_splits()
