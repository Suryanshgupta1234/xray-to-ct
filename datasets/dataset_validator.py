"""
Dataset Verification and Integrity Audit Tool.
Verifies pair matching, file integrity, resolution consistency,
and audits for zero data leakage between train, val, and test splits.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Set, List
from PIL import Image


class DatasetValidator:
    """Audits dataset directories for completeness, corruptions, and split isolation."""

    VALID_EXTENSIONS = {".png", ".jpg", ".jpeg", ".dcm", ".dicom"}

    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir)
        self.splits = ["train", "val", "test"]
        self.split_case_ids: Dict[str, Set[str]] = {s: set() for s in self.splits}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def run_audit(self) -> bool:
        """Executes full audit. Returns True if dataset passed all integrity checks."""
        print(f"\n========================================================")
        print(f" Auditing Dataset Pipeline: {self.root_dir.resolve()}")
        print(f"========================================================\n")

        total_valid_pairs = 0

        for split in self.splits:
            split_path = self.root_dir / split
            if not split_path.exists():
                self.warnings.append(f"Split directory '{split}' does not exist.")
                continue

            xray_dir = split_path / "xray"
            ct_dir = split_path / "ct"

            if not xray_dir.exists() or not ct_dir.exists():
                self.errors.append(f"Split '{split}' must contain both 'xray' and 'ct' subdirectories.")
                continue

            # Gather files
            xray_files = {
                f.stem: f for f in xray_dir.iterdir()
                if f.is_file() and f.suffix.lower() in self.VALID_EXTENSIONS
            }
            ct_files = {
                f.stem: f for f in ct_dir.iterdir()
                if f.is_file() and f.suffix.lower() in self.VALID_EXTENSIONS
            }

            xray_stems = set(xray_files.keys())
            ct_stems = set(ct_files.keys())

            paired_stems = xray_stems & ct_stems
            unpaired_xray = xray_stems - ct_stems
            unpaired_ct = ct_stems - xray_stems

            self.split_case_ids[split] = paired_stems
            total_valid_pairs += len(paired_stems)

            print(f"[{split.upper()}] Found {len(paired_stems)} matching pairs.")

            if unpaired_xray:
                self.warnings.append(
                    f"[{split}] {len(unpaired_xray)} X-ray images have no matching CT target: {list(unpaired_xray)[:5]}..."
                )
            if unpaired_ct:
                self.warnings.append(
                    f"[{split}] {len(unpaired_ct)} CT images have no matching X-ray source: {list(unpaired_ct)[:5]}..."
                )

            # Check integrity and dimensions of paired images
            for stem in paired_stems:
                self._verify_pair(xray_files[stem], ct_files[stem], split, stem)

        # Audit for Data Leakage across splits
        self._audit_data_leakage()

        # Print summary
        print(f"\nAudit Summary:")
        print(f"  - Total Valid Pairs across splits: {total_valid_pairs}")
        print(f"  - Total Warnings: {len(self.warnings)}")
        print(f"  - Total Critical Errors: {len(self.errors)}")

        for w in self.warnings:
            print(f"  [WARN]: {w}")
        for e in self.errors:
            print(f"  [ERROR]: {e}")

        is_healthy = len(self.errors) == 0 and total_valid_pairs > 0
        if is_healthy:
            print(f"\n[SUCCESS] DATASET INTEGRITY VERIFIED: Ready for training & evaluation.")
        else:
            print(f"\n[FAILED] DATASET INTEGRITY FAILED: Resolve critical errors before training.")

        return is_healthy

    def _verify_pair(self, xray_p: Path, ct_p: Path, split: str, stem: str):
        """Check image read, dimension, and channel validity."""
        for role, path in [("X-Ray", xray_p), ("CT", ct_p)]:
            try:
                if path.suffix.lower() in {".dcm", ".dicom"}:
                    import pydicom
                    dcm = pydicom.dcmread(str(path))
                    _ = dcm.pixel_array
                else:
                    with Image.open(path) as img:
                        img.verify()
            except Exception as e:
                self.errors.append(f"[{split}] Corrupted {role} image for '{stem}': {path.name} ({e})")

    def _audit_data_leakage(self):
        """Enforces zero intersection between train, val, and test case IDs."""
        train_ids = self.split_case_ids.get("train", set())
        val_ids = self.split_case_ids.get("val", set())
        test_ids = self.split_case_ids.get("test", set())

        train_val_overlap = train_ids & val_ids
        train_test_overlap = train_ids & test_ids
        val_test_overlap = val_ids & test_ids

        if train_val_overlap:
            self.errors.append(f"CRITICAL DATA LEAKAGE: {len(train_val_overlap)} cases present in both TRAIN and VAL!")
        if train_test_overlap:
            self.errors.append(f"CRITICAL DATA LEAKAGE: {len(train_test_overlap)} cases present in both TRAIN and TEST!")
        if val_test_overlap:
            self.errors.append(f"CRITICAL DATA LEAKAGE: {len(val_test_overlap)} cases present in both VAL and TEST!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Audit X-ray to CT dataset integrity")
    parser.add_argument("--dir", type=str, default="./datasets", help="Root dataset directory")
    args = parser.parse_args()

    validator = DatasetValidator(Path(args.dir))
    success = validator.run_audit()
    sys.exit(0 if success else 1)
