# ==============================================================================
# Unified Production Dockerfile (Hugging Face Spaces / Render / Railway / Local)
# Full-Stack X-Ray to CT Volumetric Translation System & PACS Workstation
# ==============================================================================

# Stage 1: Build the React 18 PACS Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python 3.11 Runtime
FROM python:3.11-slim AS production

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    ENVIRONMENT=production \
    DEVICE=cpu \
    ACTIVE_MODEL_VERSION=v1 \
    MODEL_DIR=/app/models \
    LOCAL_STORAGE_PATH=/app/storage

WORKDIR /app

# Install system dependencies for OpenCV and medical imaging
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU directly first to avoid huge 3GB CUDA binaries on free cloud hosts
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install backend dependencies
COPY backend/requirements.txt ./
# Filter out torch/torchvision from requirements since already installed
RUN grep -v -E "torch|torchvision" requirements.txt > req_notorch.txt && pip install --no-cache-dir -r req_notorch.txt

# Copy backend app, ml engine, and datasets
COPY backend/app /app/app
COPY ml /app/ml
COPY models /app/models
COPY datasets /app/datasets

# Copy built frontend assets into backend static folder
COPY --from=frontend-builder /build/dist /app/app/static

# Create unprivileged user and storage directories
RUN adduser --disabled-password --gecos "" appuser \
    && mkdir -p /app/storage /app/models \
    && chown -R appuser:appuser /app

USER appuser

# Expose default port (7860 for Hugging Face Spaces / custom PORT for Render/Railway)
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7860}/api/v1/health || exit 1

# Start Uvicorn bound to dynamic PORT
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
