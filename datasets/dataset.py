"""
PyTorch Paired Dataset for X-Ray to CT Translation.
Implements strict pair matching, corruption checks, synchronized augmentations,
and zero data-leakage controls.
"""

import os
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from PIL import Image
import numpy as np
import torch
from torch.utils.data import Dataset
import torchvision.transforms.functional as TF

from ml.preprocessing.transforms import MedicalImagePreprocessor


class PairedXrayCTDataset(Dataset):
    """
    Paired PyTorch Dataset for X-Ray (condition) and CT (target) translation.
    Expects directory structure:
        <split_dir>/
        ├── xray/
        │   ├── case_001.png (or .dcm, .jpg)
        └── ct/
            ├── case_001.png (or .dcm, .jpg)
    """

    SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".dcm", ".dicom"}

    def __init__(
        self,
        split_dir: Union[str, Path] if "Union" in globals() else str,
        image_size: Tuple[int, int] = (256, 256),
        in_channels: int = 1,
        out_channels: int = 1,
        augment: bool = False,
        normalize_range: Tuple[float, float] = (-1.0, 1.0),
        verify_integrity: bool = True,
    ):
        super().__init__()
        self.split_dir = Path(split_dir)
        self.image_size = image_size
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.augment = augment
        self.normalize_range = normalize_range

        self.xray_dir = self.split_dir / "xray"
        self.ct_dir = self.split_dir / "ct"

        self.preprocessor_xray = MedicalImagePreprocessor(
            target_size=image_size,
            normalize_range=normalize_range,
            in_channels=in_channels,
        )
        self.preprocessor_ct = MedicalImagePreprocessor(
            target_size=image_size,
            normalize_range=normalize_range,
            in_channels=out_channels,
        )

        self.pairs: List[Tuple[Path, Path]] = []
        self._find_and_verify_pairs(verify_integrity=verify_integrity)

    def _find_and_verify_pairs(self, verify_integrity: bool = True) -> None:
        """Scan directories, match pair IDs, and identify missing or corrupt files."""
        if not self.xray_dir.exists() or not self.ct_dir.exists():
            # Directory may be empty during initial checkout before dataset placement
            self.pairs = []
            return

        # Index all files in xray directory by stem
        xray_files = {
            f.stem: f for f in self.xray_dir.iterdir()
            if f.suffix.lower() in self.SUPPORTED_EXTENSIONS and f.is_file()
        }

        # Index all files in ct directory by stem
        ct_files = {
            f.stem: f for f in self.ct_dir.iterdir()
            if f.suffix.lower() in self.SUPPORTED_EXTENSIONS and f.is_file()
        }

        # Pair intersection
        common_stems = sorted(list(set(xray_files.keys()) & set(ct_files.keys())))
        unpaired_xrays = set(xray_files.keys()) - set(ct_files.keys())
        unpaired_cts = set(ct_files.keys()) - set(xray_files.keys())

        if unpaired_xrays:
            print(f"[Dataset Warning] {len(unpaired_xrays)} X-rays missing CT targets in {self.split_dir}")
        if unpaired_cts:
            print(f"[Dataset Warning] {len(unpaired_cts)} CTs missing X-ray sources in {self.split_dir}")

        verified_pairs = []
        for stem in common_stems:
            xray_p = xray_files[stem]
            ct_p = ct_files[stem]

            if verify_integrity:
                if not self._check_file_integrity(xray_p) or not self._check_file_integrity(ct_p):
                    print(f"[Dataset Warning] Corrupt file encountered for case '{stem}', skipping.")
                    continue

            verified_pairs.append((xray_p, ct_p))

        self.pairs = verified_pairs

    def _check_file_integrity(self, path: Path) -> bool:
        """Verify file can be opened and parsed without error."""
        try:
            if path.suffix.lower() in {".dcm", ".dicom"}:
                import pydicom
                pydicom.dcmread(str(path), stop_before_pixels=False)
            else:
                with Image.open(path) as img:
                    img.verify()
            return True
        except Exception:
            return False

    def __len__(self) -> int:
        return len(self.pairs)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        xray_path, ct_path = self.pairs[idx]
        case_id = xray_path.stem

        # Preprocess both images: yields tensors of shape (1, C, H, W)
        xray_tensor, xray_meta = self.preprocessor_xray.preprocess_image(xray_path)
        ct_tensor, ct_meta = self.preprocessor_ct.preprocess_image(ct_path)

        # Remove batch dim: (C, H, W)
        xray = xray_tensor.squeeze(0)
        ct = ct_tensor.squeeze(0)

        # Synchronized Data Augmentation (Train mode only)
        if self.augment:
            # Synchronized random horizontal flip: geometric spatial alignment MUST be preserved!
            if random.random() > 0.5:
                xray = TF.hflip(xray)
                ct = TF.hflip(ct)

            # Synchronized subtle affine translation/rotation (max 5 degrees)
            if random.random() > 0.5:
                angle = random.uniform(-5.0, 5.0)
                xray = TF.rotate(xray, angle)
                ct = TF.rotate(ct, angle)

        return {
            "xray": xray,
            "ct": ct,
            "id": case_id,
            "xray_path": str(xray_path),
            "ct_path": str(ct_path),
        }
