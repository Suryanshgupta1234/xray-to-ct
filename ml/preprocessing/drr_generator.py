"""
Digitally Reconstructed Radiograph (DRR) and Multi-Slice CT Volume Generator.
Implements clinical ray-sum attenuation projection through 3D CT volumes (NIfTI / Hounsfield Units)
to synthesize realistic 2D planar radiographs and paired axial CT slices.
"""

import os
import cv2
import numpy as np
import torch
from typing import Tuple, List, Optional, Union
try:
    import nibabel as nib
except ImportError:
    nib = None


def normalize_medical_image(img: np.ndarray) -> np.ndarray:
    """
    Robust medical percentile normalization to [0, 255] uint8.
    Matches the clinical CT/DRR preprocessing standard.
    """
    img = img.astype(np.float32)
    low = np.percentile(img, 1)
    high = np.percentile(img, 99)
    if high <= low:
        high = low + 1e-5
    img = np.clip(img, low, high)
    img = (img - low) / (high - low + 1e-8)
    return (img * 255.0).astype(np.uint8)


def make_synthetic_xray(volume: np.ndarray, projection_axis: int = 2) -> np.ndarray:
    """
    Simulates a 2D Digitally Reconstructed Radiograph (DRR) from a 3D CT volume
    using forward ray-sum attenuation physics.

    Args:
        volume: 3D numpy array in Hounsfield Units (HU)
        projection_axis: Axis along which rays penetrate (default 2 for axial/coronal stack)

    Returns:
        2D normalized projection radiograph (uint8, 0-255)
    """
    # Replace any invalid values
    volume = np.nan_to_num(volume)

    # Approximate medical CT diagnostic window [-1000 HU (Air) to 1200 HU (Dense Bone)]
    volume = np.clip(volume, -1000.0, 1200.0)

    # Convert to normalized linear attenuation coefficients: mu ~ (HU + 1000) / 2200.0
    attenuation = (volume + 1000.0) / 2200.0

    # Beer-Lambert forward line-integral ray summation through the volume
    projection = np.sum(attenuation, axis=projection_axis)

    # Medical contrast percentile normalization
    projection = normalize_medical_image(projection)
    return projection


def make_ct_slice(volume: np.ndarray, slice_idx: Optional[int] = None) -> np.ndarray:
    """
    Extracts and window-normalizes an axial CT slice from a 3D volume.
    """
    volume = np.nan_to_num(volume)
    if slice_idx is None:
        slice_idx = volume.shape[2] // 2

    slice_idx = max(0, min(volume.shape[2] - 1, slice_idx))
    ct = volume[:, :, slice_idx]
    ct = np.clip(ct, -1000.0, 1200.0)
    ct = normalize_medical_image(ct)
    return ct


def make_ct_slices(volume: np.ndarray, num_slices: int = 16) -> List[np.ndarray]:
    """
    Extracts an evenly spaced multi-slice volumetric stack across the 3D volume.
    """
    depth = volume.shape[2]
    indices = np.linspace(int(depth * 0.1), int(depth * 0.9), num_slices, dtype=int)
    slices = []
    for idx in indices:
        s = make_ct_slice(volume, idx)
        s_resized = cv2.resize(s, (256, 256), interpolation=cv2.INTER_AREA)
        slices.append(s_resized)
    return slices


def create_realistic_brain_ct_volume(size: Tuple[int, int, int] = (128, 128, 64)) -> np.ndarray:
    """
    Generates a realistic 3D volumetric Brain CT phantom in calibrated Hounsfield Units:
      - Air (background & sinus): -1000 HU
      - Calvarium & Skull Bone: +900 to +1150 HU
      - Brain Parenchyma (Gray/White matter): +30 to +45 HU
      - Cerebrospinal Fluid (CSF & Ventricles): 0 to +15 HU
    """
    H, W, D = size
    volume = np.full((H, W, D), -1000.0, dtype=np.float32)

    y, x, z = np.ogrid[:H, :W, :D]
    center_y, center_x, center_z = H / 2.0, W / 2.0, D / 2.0

    # 1. Cranial Skull (Ellipsoid)
    # Radii in y, x, z
    ry_outer, rx_outer, rz_outer = H * 0.44, W * 0.38, D * 0.46
    ry_inner, rx_inner, rz_inner = ry_outer - (H * 0.045), rx_outer - (W * 0.045), rz_outer - (D * 0.04)

    outer_dist = ((y - center_y) / ry_outer) ** 2 + ((x - center_x) / rx_outer) ** 2 + ((z - center_z) / rz_outer) ** 2
    inner_dist = ((y - center_y) / ry_inner) ** 2 + ((x - center_x) / rx_inner) ** 2 + ((z - center_z) / rz_inner) ** 2

    # Calvarium bone (+1000 HU)
    bone_mask = (outer_dist <= 1.0) & (inner_dist > 1.0)
    volume[bone_mask] = 1050.0 + np.random.normal(0, 40, size=np.count_nonzero(bone_mask))

    # 2. Brain Parenchyma (+38 HU)
    brain_mask = inner_dist <= 1.0
    volume[brain_mask] = 38.0 + np.random.normal(0, 5, size=np.count_nonzero(brain_mask))

    # 3. Lateral Ventricles & Third Ventricle (CSF: +5 HU)
    # Two curved horns near center
    for sign in [-1, 1]:
        vent_center_x = center_x + sign * (W * 0.08)
        vent_center_y = center_y - (H * 0.03)
        vent_dist = (((y - vent_center_y) / (H * 0.16)) ** 2 +
                     ((x - vent_center_x) / (W * 0.05)) ** 2 +
                     ((z - center_z) / (D * 0.28)) ** 2)
        vent_mask = vent_dist <= 1.0
        volume[vent_mask] = 8.0 + np.random.normal(0, 2, size=np.count_nonzero(vent_mask))

    # Third ventricle midline slit
    midline_vent = (np.abs(x - center_x) <= 2) & (np.abs(y - center_y) <= H * 0.1) & (np.abs(z - center_z) <= D * 0.2)
    volume[midline_vent] = 6.0

    return volume


def create_realistic_chest_ct_volume(size: Tuple[int, int, int] = (128, 128, 64)) -> np.ndarray:
    """
    Generates a realistic 3D volumetric Thoracic Chest CT phantom in calibrated Hounsfield Units:
      - Air / Background: -1000 HU
      - Lung Parenchyma: -750 to -850 HU
      - Thoracic Cage & Ribs: +800 to +1100 HU
      - Spine / Vertebra: +700 to +950 HU
      - Mediastinum & Heart: +40 to +60 HU
    """
    H, W, D = size
    volume = np.full((H, W, D), -1000.0, dtype=np.float32)

    y, x, z = np.ogrid[:H, :W, :D]
    center_y, center_x, center_z = H / 2.0, W / 2.0, D / 2.0

    # Thoracic Wall & Soft Tissue Ellipsoid (+45 HU)
    ry, rx, rz = H * 0.44, W * 0.46, D * 0.48
    body_dist = ((y - center_y) / ry) ** 2 + ((x - center_x) / rx) ** 2 + ((z - center_z) / rz) ** 2
    body_mask = body_dist <= 1.0
    volume[body_mask] = 45.0 + np.random.normal(0, 8, size=np.count_nonzero(body_mask))

    # Rib cage & Sternum (Bone: +900 HU)
    rib_mask = (body_dist <= 1.0) & (body_dist >= 0.88) & ((z % 4) < 2)
    volume[rib_mask] = 950.0 + np.random.normal(0, 50, size=np.count_nonzero(rib_mask))

    # Thoracic Spine (+850 HU)
    spine_mask = (np.abs(x - center_x) <= W * 0.07) & (y >= center_y + H * 0.25) & (y <= center_y + H * 0.42) & (z >= 0)
    volume[spine_mask] = 850.0

    # Bilateral Lung Fields (Hypodense: -800 HU)
    for sign in [-1, 1]:
        lung_center_x = center_x + sign * (W * 0.22)
        lung_center_y = center_y
        lung_dist = (((y - lung_center_y) / (H * 0.32)) ** 2 +
                     ((x - lung_center_x) / (W * 0.16)) ** 2 +
                     ((z - center_z) / (D * 0.40)) ** 2)
        lung_mask = lung_dist <= 1.0
        volume[lung_mask] = -800.0 + np.random.normal(0, 30, size=np.count_nonzero(lung_mask))

    # Central Heart / Cardiac Shadow (+50 HU)
    heart_center_x = center_x - (W * 0.05)
    heart_center_y = center_y + (H * 0.08)
    heart_dist = (((y - heart_center_y) / (H * 0.18)) ** 2 +
                  ((x - heart_center_x) / (W * 0.15)) ** 2 +
                  ((z - (center_z - D * 0.05)) / (D * 0.25)) ** 2)
    heart_mask = heart_dist <= 1.0
    volume[heart_mask] = 50.0 + np.random.normal(0, 6, size=np.count_nonzero(heart_mask))

    return volume


def generate_realistic_paired_dataset(
    output_dir: str,
    num_samples: int = 30,
    img_size: int = 256,
) -> Tuple[str, str]:
    """
    Synthesizes paired realistic (X-Ray DRR, CT slice, multi-slice) dataset
    matching the Google Colab workflow shared by the user.

    Returns:
        Tuple of (xray_dir, ct_dir)
    """
    pair_xray_dir = os.path.join(output_dir, "xray")
    pair_ct_dir = os.path.join(output_dir, "ct")
    os.makedirs(pair_xray_dir, exist_ok=True)
    os.makedirs(pair_ct_dir, exist_ok=True)

    print(f"[DRR Generator] Synthesizing {num_samples} realistic clinical CT volumes and projection pairs...")

    for i in range(num_samples):
        # Alternate between Brain CT and Chest CT scans for rich diversity
        if i % 2 == 0:
            volume = create_realistic_brain_ct_volume()
            # Sagittal/axial projection through volume
            xray = make_synthetic_xray(volume, projection_axis=2)
            ct = make_ct_slice(volume)
        else:
            volume = create_realistic_chest_ct_volume()
            xray = make_synthetic_xray(volume, projection_axis=1)
            ct = make_ct_slice(volume)

        xray_resized = cv2.resize(xray, (img_size, img_size), interpolation=cv2.INTER_AREA)
        ct_resized = cv2.resize(ct, (img_size, img_size), interpolation=cv2.INTER_AREA)

        filename = f"{i:04d}.png"
        cv2.imwrite(os.path.join(pair_xray_dir, filename), xray_resized)
        cv2.imwrite(os.path.join(pair_ct_dir, filename), ct_resized)

    print(f"[DRR Generator] Successfully generated {num_samples} pairs in {output_dir}")
    return pair_xray_dir, pair_ct_dir


if __name__ == "__main__":
    out = "data/realistic_pairs"
    generate_realistic_paired_dataset(out, num_samples=30)
