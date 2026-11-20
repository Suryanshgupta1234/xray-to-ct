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

---

## 5. 100% Free Cloud Deployment Guide

You can deploy this entire Machine Learning and PACS Web application completely free using either **Hugging Face Spaces** (recommended for AI/ML with 16 GB free RAM) or **Render.com**.

### Option A: Hugging Face Spaces (Recommended — Free 16 GB RAM + Public URL)

Hugging Face Spaces provides **free 2 vCPU, 16 GB RAM**, which is ideal for PyTorch medical image translation and multi-slice volumetric CT reconstruction.

#### Step 1: Create a New Space
1. Sign in or register at [huggingface.co](https://huggingface.co) (free).
2. Click your profile icon at top-right and select **New Space** (or go to `huggingface.co/new-space`).
3. Set:
   - **Space Name**: `xray-to-ct-pacs`
   - **License**: `MIT`
   - **Space SDK**: Select **Docker** -> **Blank**
   - **Space Hardware**: Choose **CPU basic (2 vCPU · 16 GB RAM · Free)**
   - **Visibility**: Public or Private
4. Click **Create Space**.

#### Step 2: Push the Repository
In your local project terminal, link your Hugging Face Space repository:

```bash
cd c:\Users\siddh\OneDrive\Desktop\money\xray-to-ct

# 1. Add your Hugging Face Space as a git remote (replace <username> with your HF username)
git remote add space https://huggingface.co/spaces/<your-username>/xray-to-ct-pacs

# 2. Push to Hugging Face
git push space master:main
```

*(If prompted for credentials, use your Hugging Face username and your Access Token from `huggingface.co/settings/tokens`).*

#### Step 3: Done!
* Hugging Face will automatically execute the multi-stage [`Dockerfile`](file:///c:/Users/siddh/OneDrive/Desktop/money/xray-to-ct/Dockerfile), compile the React 18 PACS frontend, load the PyTorch U-Net weights, and launch the application on port `7860`.
* Your app will be live at:
  `https://huggingface.co/spaces/<your-username>/xray-to-ct-pacs`

---

### Option B: Render.com (Free Web Service via GitHub)

#### Step 1: Push Project to GitHub
1. Create a repository on GitHub (e.g. `xray-to-ct`).
2. Push your project:
   ```bash
   cd c:\Users\siddh\OneDrive\Desktop\money\xray-to-ct
   git remote add origin https://github.com/<your-username>/xray-to-ct.git
   git push -u origin master
   ```

#### Step 2: Deploy on Render
1. Sign in to [render.com](https://render.com) using your GitHub account.
2. Click **New +** -> **Web Service**.
3. Select your `xray-to-ct` GitHub repository.
4. Render will auto-detect the [`render.yaml`](file:///c:/Users/siddh/OneDrive/Desktop/money/xray-to-ct/render.yaml) file or choose:
   - **Environment**: Docker
   - **Instance Type**: Free
   - **Health Check Path**: `/api/v1/health`
5. Click **Create Web Service**.
6. Render builds the Docker image and provides a free HTTPS URL: `https://xray-to-ct-pacs.onrender.com`.

---

### Option C: Instant Free Public URL via Cloudflare Tunnel (Zero Cloud Setup)

If you want to share your running application right now with a collaborator or professor without building on the cloud:

```bash
# In your terminal, run Cloudflare Tunnel directly:
npx cloudflared tunnel --url http://localhost:8000
```
This gives you an instant free, secure `https://<random-subdomain>.trycloudflare.com` URL that tunnels directly to your local application with both the frontend PACS and API!

