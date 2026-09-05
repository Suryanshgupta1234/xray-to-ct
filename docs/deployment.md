# Production Deployment & Cloud Infrastructure Guide

## 1. Cloud Architecture Overview

The system is designed for horizontal scalability, decoupling stateless compute nodes from persistence and object storage.

```mermaid
flowchart TD
    Client[Web Browser Client] --> CDN[Cloudflare / Vercel Edge CDN]
    CDN --> Frontend[React 18 Static SPA]
    Frontend --> LB[Cloud Load Balancer / Ingress]
    LB --> Backend1[FastAPI + PyTorch Node 1 (GPU EC2/G4dn)]
    LB --> Backend2[FastAPI + PyTorch Node 2 (GPU EC2/G4dn)]
    Backend1 --> S3[(AWS S3 / Cloudflare R2)]
    Backend2 --> S3
    Backend1 --> DB[(AWS RDS PostgreSQL 16)]
    Backend2 --> DB
    Backend1 --> Redis[(ElastiCache Redis)]
    Backend2 --> Redis
```

---

## 2. Target Deployment Topologies

| Tier | Recommended Platform | Configuration & Sizing |
| :--- | :--- | :--- |
| **Frontend SPA** | Vercel / Cloudflare Pages / AWS S3 + CloudFront | Static Jamstack bundle (`npm run build`), automatic SSL, global edge caching. |
| **Backend & Inference** | AWS ECS / EKS / Render / Railway | `g4dn.xlarge` (NVIDIA T4 16GB VRAM) or `c6i.2xlarge` (CPU baseline). |
| **Relational Database** | AWS RDS / Neon / Supabase | PostgreSQL 16 managed instance with automated backups and read replicas. |
| **Asset Storage** | AWS S3 / Cloudflare R2 / MinIO | Encrypted bucket with CORS rules allowing browser downloads. |
| **Cache & Tasks** | Redis Cloud / AWS ElastiCache | In-memory key-value store for session rate limits and Celery workers. |

---

## 3. Docker Compose Orchestration (Local & Self-Hosted)

To launch the complete unified stack locally or on a private server:

```bash
# 1. Clone repository
git clone https://github.com/organization/xray-to-ct.git
cd xray-to-ct

# 2. Configure environment
cp .env.example .env

# 3. Launch stack
docker compose up --build -d
```

Services will be online at:
- **Frontend Dashboard**: `http://localhost:3000`
- **FastAPI REST API**: `http://localhost:8000`
- **Interactive Swagger Docs**: `http://localhost:8000/api/v1/docs`

---

## 4. Hardware Sizing & GPU Acceleration

While the model features a CPU fallback for local testing, **production batch and high-throughput environments require NVIDIA GPU hardware**:
- **Latency on CPU**: ~30ms – 70ms per $256 \times 256$ slice.
- **Latency on GPU (NVIDIA T4 / A10G)**: ~4ms – 8ms per $256 \times 256$ slice.
- Set environment variable `DEVICE=cuda` and configure `nvidia-container-toolkit` for Docker runtime acceleration.
