---
title: X-Ray to CT Volumetric Translation PACS Workstation
emoji: 🩻
colorFrom: blue
colorTo: cyan
sdk: docker
app_port: 7860
pinned: false
---

# X-Ray to CT Image Translation System (Production-Grade Research Platform)

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-red.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116+-teal.svg)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18.2-61dafb.svg)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4+-purple.svg)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ed.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT_Research-yellow.svg)](./LICENSE)

---

## ⚠️ Mandatory Medical and Research Disclaimer

> **THIS SYSTEM IS A RESEARCH AND EDUCATIONAL PROTOTYPE FOR IMAGE-TO-IMAGE TRANSLATION.**
>
> The generated images and cross-sectional representations produced by this software are **AI-synthesized approximations** created by a Conditional Generative Adversarial Network (pix2pix). They are **NOT** clinically validated Computed Tomography (CT) scans, are **NOT** equivalent to true diagnostic radiology acquisitions, and have **NOT** been cleared or evaluated by any regulatory health agency (FDA, CE, EMA).
>
> **STRICT PROHIBITION**: This application must **NEVER** be used for clinical diagnosis, patient triage, surgical or radiotherapy planning, treatment monitoring, or emergency medical evaluations. The model can hallucinate structures, introduce out-of-plane artifacts, or omit critical clinical pathology present in physical biological tissue.

---

## 1. Project Overview & Motivation

Planar projection radiography (X-ray) remains the most widely accessible, cost-effective, and lowest-radiation medical imaging modality worldwide. Conversely, Computed Tomography (CT) offers cross-sectional volumetric depth and soft-tissue discrimination at the expense of higher radiation dose, specialized gantries, and greater capital cost.

This platform investigates the mathematical and computational frontiers of the ill-posed 2D-to-3D projection inversion problem. By leveraging conditional generative adversarial networks (pix2pix), the system maps 2D attenuation projections into estimated axial slice representations for educational exploration, algorithm benchmarking, and computer vision research.

---

## 2. System Architecture

```mermaid
flowchart TD
    subgraph Client ["Client Presentation Layer (React 18 + Vite + Tailwind)"]
        UI[Medical Research Dashboard]
        Viewer[Side-by-Side & Split Slider Viewer]
        Uploader[Drag-and-Drop Image Uploader]
    end

    subgraph Gateway ["API & Application Layer (FastAPI)"]
        AuthRoute[/api/v1/auth]
        InfRoute[/api/v1/inference]
        ModelRoute[/api/v1/models]
        HealthRoute[/api/v1/health]
        Security[JWT / Bcrypt / Magic Byte Validator]
    end

    subgraph Services ["Service Layer"]
        InferenceSvc[Inference Service]
        PreprocessSvc[Medical Preprocessing Pipeline]
        PostprocessSvc[Postprocessing Pipeline]
        StorageSvc[Storage Service Abstraction]
    end

    subgraph ML ["Machine Learning Core"]
        Registry[In-Memory Model Cache]
        Engine[PyTorch Inference Engine]
        Model[pix2pix U-Net Generator v1]
    end

    subgraph Data ["Data & Storage Layer"]
        DB[(PostgreSQL 16 / SQLite 3)]
        LocalStorage[(Local File Storage / AWS S3)]
        RedisCache[(Redis Cache)]
    end

    UI --> Security
    Security --> AuthRoute
    Security --> InfRoute
    Security --> ModelRoute
    Security --> HealthRoute

    InfRoute --> InferenceSvc
    InferenceSvc --> PreprocessSvc
    PreprocessSvc --> Engine
    Registry --> Engine
    Engine --> Model
    Engine --> PostprocessSvc
    PostprocessSvc --> StorageSvc
    StorageSvc --> LocalStorage
    InferenceSvc --> DB
    AuthRoute --> DB
    InferenceSvc -.-> RedisCache
```

---

## 3. Technology Stack

- **Frontend**: React 18, Vite, JavaScript (Strictly NO TypeScript), Tailwind CSS, Lucide React, Axios, React Router v6.
- **Backend API**: Python 3.13, FastAPI, Pydantic v2, Uvicorn, SQLAlchemy 2.0 Async, aiosqlite / asyncpg.
- **Machine Learning Core**: PyTorch 2.x, Torchvision, Scikit-Image, PyDICOM.
- **Security & Auth**: Pure `bcrypt` (12 rounds), HMAC-SHA256 JWT, Magic Byte binary sniffing.
- **Database & Persistence**: PostgreSQL 16 (production), SQLite 3 (zero-config local dev), Pluggable Storage (Local filesystem / AWS S3 / MinIO).
- **Containerization & CI/CD**: Multi-stage Dockerfiles, Docker Compose, GitHub Actions.

---

## 4. Machine Learning Implementation: pix2pix

The core translation engine uses a Conditional Generative Adversarial Network:

### 4.1 Generator: U-Net 256
- **Encoder**: 8 downsampling stages with `Conv2d(stride=2)`, `BatchNorm2d`, and `LeakyReLU(0.2)`.
- **Bottleneck**: $1 \times 1 \times 512$ latent feature representation.
- **Decoder with Skip Connections**: 8 upsampling stages with `ConvTranspose2d(stride=2)`, `BatchNorm2d`, `Dropout(0.5)`, and `ReLU`.
- Skip connections concatenate matching encoder features directly to decoder inputs, preserving sharp cortical bone boundaries and preventing spatial blur.
- **Output Activation**: $\tanh$ mapping synthesized pixel intensities to $[-1.0, 1.0]$.

### 4.2 Discriminator: 70×70 PatchGAN
- Evaluates conditioned input pairs $[X_{\text{xray}}, Y_{\text{ct}}]$ across a local $70 \times 70$ receptive field, outputting a $30 \times 30$ patch logit grid.
- Enforces high-frequency textural realism while leaving low-frequency structural layout to the $L_1$ loss.

### 4.3 Objective Formulation
$$\mathcal{L}_{\text{Total}} = \mathcal{L}_{\text{GAN}}(G, D) + \lambda \mathcal{L}_{L_1}(G)$$
- **$\lambda = 100.0$**: Balances structural fidelity against hallucination.
- **Least-Squares GAN (LSGAN)**: Employs MSE adversarial loss for stable gradient dynamics.

---

## 5. Dataset Pipeline & Ingestion

### Directory Layout
```text
datasets/
├── train/
│   ├── xray/
│   └── ct/
├── val/
│   ├── xray/
│   └── ct/
└── test/
    ├── xray/
    └── ct/
```

### Mock Synthetic Phantoms
To verify software workflows and CI/CD without distributing unverified clinical data, a procedural geometric phantom generator is included:
```bash
python datasets/sample_generator.py --train 24 --val 6 --test 6 --seed 42
```
Every generated phantom image is explicitly watermarked: `NON-CLINICAL PHANTOM`.

### Dataset Verification Audit
```bash
python datasets/dataset_validator.py
```
Audits pair matches, file integrity, resolution consistency, and guarantees **zero data leakage** between splits.

---

## 6. Getting Started

### Prerequisites
- Python 3.10+ (Python 3.13 supported)
- Node.js 18+ and npm 9+
- Docker & Docker Compose (optional for containerized deployment)

### 1-Click Launch (Windows)
Double-click [`scripts/run_local.bat`](./scripts/run_local.bat) to launch both the FastAPI backend and React frontend concurrently.

### Manual Local Launch

#### Step 1: Backend Setup
```bash
# Clone and enter repo
cd xray-to-ct

# Create environment config
cp .env.example .env

# Install dependencies
pip install -r backend/requirements.txt

# Start backend server
python -m uvicorn app.main:app --app-dir backend --reload --port 8000
```

#### Step 2: Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit:
- **Web Dashboard**: `http://localhost:5173`
- **Swagger API Documentation**: `http://localhost:8000/api/v1/docs`
- **System Health Check**: `http://localhost:8000/api/v1/health`

---

## 7. Model Training & Evaluation

### Train pix2pix Model
```bash
python training/train.py --config training/config.yaml --epochs 30 --batch_size 4
```
Trained generator weights and version manifest are automatically saved to `models/v1/generator.pth` and `models/v1/metadata.json`.

### Evaluate Model Fidelity
```bash
python training/evaluate.py --model models/v1/generator.pth
```
Calculates **MAE, MSE, PSNR (dB), and SSIM** across the test split and exports 4-panel visual comparison grids to `results/evaluation/`.

---

## 8. Automated Test Suite

Run unit and end-to-end integration tests:
```bash
python -m pytest tests/ -v
```

Test Coverage Includes:
- `test_generator_forward_shape`: Verifies forward pass tensor shapes and $\tanh$ bounds.
- `test_patchgan_discriminator_shape`: Verifies PatchGAN receptive field and grid dimensions.
- `test_pix2pix_loss_computation`: Confirms composite GAN + $\lambda L_1$ loss formulations.
- `test_evaluation_metrics_deterministic`: Verifies MAE, MSE, PSNR, and SSIM accuracy.
- `test_preprocessor_with_pil`: Verifies normalization to $[-1, 1]$ and resizing.
- `test_hu_windowing_formula`: Tests soft tissue, lung, and bone HU windowing.
- `test_upload_validator_magic_bytes`: Confirms rejection of spoofed files.
- `test_health_endpoint`: Checks backend service status matrix.
- `test_auth_and_inference_lifecycle`: End-to-end API lifecycle test (Register -> Login -> Upload X-ray -> Infer CT -> Query History).

---

## 9. Docker Deployment

Launch the complete containerized stack (PostgreSQL, Redis, FastAPI, Nginx React):
```bash
docker compose up --build -d
```

---

## 10. Technical Interview Guide (Key Engineering Answers)

| Question | Core Engineering Answer |
| :--- | :--- |
| **Why pix2pix instead of CycleGAN?** | CycleGAN solves *unpaired* translation and relies on cycle consistency without spatial conditioning, often causing anatomical hallucination. Pix2pix is paired and structurally conditioned on the X-ray, enforcing exact spatial anatomical alignment. |
| **Why PatchGAN over a scalar Discriminator?** | A scalar discriminator averages global structure, leading to blur. PatchGAN has a $70 \times 70$ receptive field, penalizing local high-frequency artifacts (bone edges, trabecular texture) while $L_1$ loss controls global organ placement. |
| **Why L1 Loss instead of L2 (MSE)?** | L2 loss minimizes squared errors, mathematically producing the conditional *mean* of possible states (causing washed-out, blurry averages). L1 minimizes absolute error, producing the conditional *median* and preserving sharp edge gradients. |
| **How is file upload security handled?** | Uploads are treated as untrusted. Files are checked against binary magic bytes (preventing extension renaming spoofing), restricted to 25 MB, and saved as cryptographically random UUIDs to eliminate path traversal attacks (`../../`). |
| **How does model caching work?** | A singleton `ModelRegistry` loads weights once upon startup into GPU/CPU memory and warms up CUDA kernels with a dummy tensor. Subsequent user requests execute directly from memory in $\sim 15$–$40$ms with zero disk load overhead. |
| **What is the mathematical limitation of 2D to 3D translation?** | Radiography integrates attenuation line integrals across the entire volume path into a single 2D projection. Inverting a single projection is an ill-posed mathematical inverse problem with infinite null-space solutions. The model infers a learned statistical prior rather than physical measurement. |

---

## 11. Project Documentation Index

- [`docs/architecture.md`](./docs/architecture.md) — System Architecture & Component Decoupling
- [`docs/api.md`](./docs/api.md) — REST API Reference & JSON Schemas
- [`docs/ml-pipeline.md`](./docs/ml-pipeline.md) — pix2pix Theory, Losses & Receptive Fields
- [`docs/database.md`](./docs/database.md) — Database Schema, ER Diagram & Indexing Strategy
- [`docs/deployment.md`](./docs/deployment.md) — Cloud Topologies & Production Sizing
- [`docs/security.md`](./docs/security.md) — Threat Modeling, Upload Defense & PHI Privacy
- [`datasets/README.md`](./datasets/README.md) — Real Clinical Dataset Mounting & Preprocessing
