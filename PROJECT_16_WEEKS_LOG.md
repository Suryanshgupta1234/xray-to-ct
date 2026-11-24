# 16-Week Project Work Log & Milestone Roadmap
**Project Title**: Cross-Modality Radiographic Image Translation: 2D Planar Radiograph to 3D Volumetric Pseudo-CT Synthesis and Clinical PACS Workstation  
**Author / Lead Developer**: Suryansh Gupta  
**Repository**: [github.com/Suryanshgupta1234/xray-to-ct](https://github.com/Suryanshgupta1234/xray-to-ct)  
**System Architecture**: FastAPI (Python 3.11), PyTorch (U-Net 256 + PatchGAN), React 18, Vite, Docker, Render, Vercel  

---

## 16-Week Master Timeline

| Week | Phase | Milestone / Focus | Status | Key Deliverable |
| :---: | :---: | :--- | :---: | :--- |
| **W1** | Phase 1 | Literature Review & Clinical Workflow Analysis | **DONE** | Problem definition, PACS requirements specification |
| **W2** | Phase 1 | Medical Imaging Physics & Attenuation Formulations | **DONE** | HU-to-linear attenuation mathematical model |
| **W3** | Phase 1 | Volumetric CT Ingestion & NIfTI Data Pipeline | **DONE** | 3D NIfTI loading, percentile windowing (1-99%) |
| **W4** | Phase 1 | Clinical Forward Projection (DRR Generator) | **DONE** | Ray-sum forward projection simulator (Beer-Lambert model) |
| **W5** | Phase 2 | pix2pix Architecture Design & Latent Mapping | **DONE** | 15-stage U-Net 256 generator + 70x70 PatchGAN |
| **W6** | Phase 2 | Multi-Objective Loss Function Engineering | **DONE** | Adversarial Loss + 100x L1 pixel loss implementation |
| **W7** | Phase 2 | Model Training & Checkpoint Optimization | **DONE** | 50 epochs paired training, mixed precision AMP |
| **W8** | Phase 2 | Objective Validation & Metrics Benchmark | **DONE** | MAE, PSNR, SSIM evaluation scripts & benchmarks |
| **W9** | Phase 3 | Volumetric 16-Slice Continuous Axial Synthesis | **DONE** | Z-axis deformation (-75mm to +75mm) & HU calibration |
| **W10** | Phase 3 | Hospital PACS Workstation UI & Cine Player | **DONE** | Dual-pane viewer, Scout Topogram, 5-window presets |
| **W11** | Phase 3 | Institutional Clinical Radiology Reporting Engine | **DONE** | HU telemetry, tissue density bars, print PDF styling |
| **W12** | Phase 3 | Full-Stack Security, Auth, & REST API Pipeline | **DONE** | Async FastAPI, SQLite/asyncpg, bcrypt, JWT auth |
| **W13** | Phase 3 | **Cloud Deployment, Memory Optimization & CORS** | **CURRENT** | Dockerized Render backend, Vercel frontend, 512MB RAM fix |
| **W14** | Phase 4 | **Multi-Planar Reconstruction (MPR) & DICOM Export** | **NEXT WEEK** | Sagittal/Coronal views, standard .dcm export |
| **W15** | Phase 4 | Blinded Radiologist Survey & Clinical Evaluation | **PLANNED** | Trainee perceptual survey, quantitative fidelity paper |
| **W16** | Phase 4 | Project Final Report, Open-Source Release & Defense | **PLANNED** | Final thesis submission, demo video, project defense |
