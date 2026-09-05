# X-Ray to CT Image Translation System (Research & Educational Platform)

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.x-red.svg)](https://pytorch.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-teal.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-blue.svg)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.4+-purple.svg)](https://tailwindcss.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT_Research-yellow.svg)](./LICENSE)

---

## ⚠️ Important Medical and Research Disclaimer

> **THIS SYSTEM IS A RESEARCH AND EDUCATIONAL PROTOTYPE FOR IMAGE-TO-IMAGE TRANSLATION.**
>
> The generated representations produced by this software are **AI-synthesized approximations** created by a Conditional Generative Adversarial Network (pix2pix). They are **NOT** clinically validated Computed Tomography (CT) scans, are **NOT** equivalent to true radiologic diagnostic imaging, and have **NOT** been evaluated or cleared by any regulatory health agency (FDA, CE, EMA).
>
> **STRICT PROHIBITION**: This application must **NOT** be used for primary diagnostic interpretation, treatment or surgical planning, clinical decision-making, patient triage, or emergency medical evaluations. The model can introduce out-of-plane artifacts, hallucinate structures, or omit critical clinical pathology present in physical tissues.

---

## 1. Project Overview & Motivation

Planar projection radiography (X-ray) remains the most accessible, cost-effective, and low-dose medical imaging modality worldwide. Computed Tomography (CT), while providing cross-sectional volumetric visualization with soft-tissue and anatomical depth, involves significantly higher radiation doses, capital costs, and specialized infrastructure.

The **X-Ray to CT Image Translation System** explores the mathematical and machine learning frontiers of the ill-posed 2D-to-3D projection inversion problem. By leveraging conditional GAN architectures (pix2pix), the system models structural correlations between 2D attenuation projections and corresponding cross-sectional synthetic CT representations for educational exploration and research prototyping.

---

## 2. Monorepo Repository Structure

```text
xray-to-ct/
├── frontend/             # React 18 + Vite + Tailwind CSS dashboard (Vanilla JS)
├── backend/              # FastAPI REST API, auth, and database persistence
│   ├── app/
│   │   ├── api/routes/   # REST endpoint routers (auth, inference, models, health)
│   │   ├── core/         # Settings, JWT security, structured logging
│   │   ├── models/       # SQLAlchemy database entity models
│   │   ├── schemas/      # Pydantic validation and serialization schemas
│   │   ├── services/     # Inference, preprocessing, postprocessing, storage
│   │   ├── ml/           # Model loader, runtime predictor, model registry
│   │   └── utils/        # Image validators, magic bytes, helper functions
│   └── requirements.txt
├── ml/                   # Machine learning core library (independent of API)
│   ├── models/           # pix2pix Generator (U-Net) & Discriminator (PatchGAN)
│   └── preprocessing/    # Medical DICOM handling & intensity transforms
├── training/             # PyTorch training loop, losses, evaluation metrics
├── datasets/             # Data ingestion interfaces & mock dataset generators
├── models/               # Model weights store (v1, v2) with metadata manifests
├── tests/                # Unit and integration test suites
├── docs/                 # Architectural specifications, APIs, and ML theory
├── scripts/              # Developer automation scripts
├── docker-compose.yml    # Full-stack multi-container composition
├── .env.example          # Environment variable template
└── LICENSE               # MIT License with research non-clinical rider
```

---

## 3. Technology Stack

- **Frontend**: React 18, Vite, JavaScript (Strictly NO TypeScript), Tailwind CSS, React Router v6, Axios, Lucide React icons.
- **Backend API**: Python 3.13, FastAPI, Pydantic v2, Uvicorn, SQLAlchemy 2.0 (async), Alembic.
- **Machine Learning Core**: PyTorch 2.x, Torchvision, Scikit-Image, PyDICOM.
- **Database & Storage**: PostgreSQL 16 (production), SQLite 3 (zero-config local fallback), Pluggable Storage (Local filesystem / AWS S3 / MinIO).
- **Orchestration**: Docker, Docker Compose.

---

## 4. Getting Started

### Prerequisites
- Python 3.10+ (Python 3.13 supported)
- Node.js 18+ and npm 9+
- Git

### Quick Setup

1. **Clone and setup repository**:
   ```bash
   cd xray-to-ct
   cp .env.example .env
   ```

2. **Backend Setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

3. **Frontend Setup**:
   ```bash
   cd ../frontend
   npm install
   npm run dev
   ```

Visit `http://localhost:5173` to explore the dashboard and `http://localhost:8000/docs` for the interactive Swagger OpenAPI documentation.

---

## 5. Development Phases

- **Phase 1: Architecture & Repository Structure** (Completed)
- **Phase 2: Dataset Pipeline & Preprocessing**
- **Phase 3: pix2pix Model Architecture**
- **Phase 4: Training Pipeline & Losses**
- **Phase 5: Evaluation & Metrics Engine**
- **Phase 6: FastAPI Backend REST API**
- **Phase 7: Database & JWT Authentication**
- **Phase 8: Modern React Frontend**
- **Phase 9: Production Inference Integration**
- **Phase 10: Dockerization & Orchestration**
- **Phase 11: Automated Test Suite**
- **Phase 12: Production Hardening & Health Monitoring**
- **Phase 13: Comprehensive Docs & Interview Guide**
