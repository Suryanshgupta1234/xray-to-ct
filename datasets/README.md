# Dataset Pipeline & Ingestion Guide

## 1. Directory Structure

The dataset pipeline expects paired data arranged into three distinct partitions:

```text
datasets/
├── train/
│   ├── xray/           # 2D planar projection radiographs (PNG, JPEG, or DICOM)
│   │   ├── case_001.png
│   │   └── case_002.png
│   └── ct/             # Corresponding cross-sectional CT slices (PNG, JPEG, or DICOM)
│       ├── case_001.png
│       └── case_002.png
│
├── val/
│   ├── xray/
│   └── ct/
│
└── test/
    ├── xray/
    └── ct/
```

### Pairing Convention
Files in `xray/` and `ct/` must share the **exact same base filename stem** (e.g., `patient_402.png` in `xray/` pairs with `patient_402.png` in `ct/`). The file extensions may vary (`.dcm`, `.png`, `.jpg`), but matching stems are required.

---

## 2. Real Clinical Dataset Integration

To train this translation model on real medical data:

1. **Eligible Datasets**:
   - **LIDC-IDRI** (Lung Image Database Consortium): Contains 3D volumetric thoracic CT scans. Paired 2D Digitally Reconstructed Radiographs (DRRs) can be computed via ray-casting / Radon transform projection.
   - **DeepDRR / OpenDRR Projections**: Forward-projected radiographs paired with central axial CT slices.
   - **Paired Bi-planar X-ray / CT Studies**: Institutional de-identified paired acquisitions.

2. **Mounting Instructions**:
   Place your verified clinical pairs directly into `datasets/train/`, `datasets/val/`, and `datasets/test/` following the directory structure above.
   Ensure that files are stripped of all Protected Health Information (PHI) before placing them into the repository.

3. **Audit Before Training**:
   Run the integrity validator before launching training:
   ```bash
   python datasets/dataset_validator.py --dir ./datasets
   ```

---

## 3. Synthetic Mock Dataset for Development

To facilitate software engineering, pipeline verification, API testing, and CI/CD without distributing multi-gigabyte unverified patient data:

Run the mock dataset generator:
```bash
python datasets/sample_generator.py --train 24 --val 6 --test 6 --seed 42
```
> **Disclaimer**: The mock generator creates mathematical geometric phantoms (elliptical thoracic boundaries, simulated rib silhouettes, and axial slice profiles). Every generated image is watermarked `NON-CLINICAL PHANTOM`. They are strictly for software validation.

---

## 4. Preprocessing Decisions & Rationale

| Preprocessing Step | Decision | Clinical & ML Rationale |
| :--- | :--- | :--- |
| **Target Resolution** | $256 \times 256$ pixels | Balances structural anatomical resolution with memory efficiency during GAN training and fast CPU/GPU inference latency (<100ms). |
| **Color Channels** | Single-channel grayscale ($C=1$) | Radiographs and CT scans are intrinsically scalar attenuation measurements. Processing them in grayscale avoids artificial RGB channel bias and cuts parameter memory by $\frac{2}{3}$. |
| **Normalization Range** | $[-1.0, 1.0]$ | Symmetrical dynamic range centered at zero is optimal for the Generator's final $\tanh$ activation function, stabilizing GAN gradient backpropagation. |
| **CT Hounsfield Unit Windowing** | Configurable presets (Mediastinum: $C=40, W=400$, Lung: $C=-600, W=1500$, Bone: $C=400, W=1800$) | Raw CT scans span $-1024$ to $+3071$ HU. Clinical windowing isolates tissue attenuation of interest and clips irrelevant outliers before tensor scaling. |
| **Synchronized Augmentation** | Paired horizontal flipping & minor affine rotation | Translation models require pixel-to-pixel spatial correspondence. Augmentations must be applied identically to both condition (X-ray) and target (CT) simultaneously. |
| **Zero Data Leakage** | Patient-level stem partition isolation | Audited by `dataset_validator.py`. A patient/case ID must never appear in more than one partition to prevent overoptimistic evaluation metrics. |
