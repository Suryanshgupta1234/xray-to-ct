"""
Integration Tests for FastAPI REST API Endpoints.
Uses FastAPI TestClient for clean, deterministic synchronous test execution.
"""

import sys
import io
import asyncio
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.models.base import init_db

# Initialize database tables once synchronously
asyncio.run(init_db())

client = TestClient(app)


def test_health_endpoint():
    """Tests /api/v1/health returns HTTP 200 and healthy statuses."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["api"]["status"] == "healthy"
    assert "device" in data["data"]


def test_auth_and_inference_lifecycle():
    """Full lifecycle: Register -> Login -> Upload X-Ray -> View CT Result -> Check History."""
    # 1. Register
    reg_payload = {
        "email": "lifecycle_tester@lab.edu",
        "password": "SecurePassword123!",
        "full_name": "Lifecycle Tester",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code in (201, 400)

    # 2. Login
    login_payload = {
        "email": "lifecycle_tester@lab.edu",
        "password": "SecurePassword123!",
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Query Models
    models_res = client.get("/api/v1/models")
    assert models_res.status_code == 200
    assert len(models_res.json()["data"]) >= 1

    # 4. Generate in-memory X-ray test image
    img_buf = io.BytesIO()
    test_img = Image.new("L", (256, 256), color=80)
    test_img.save(img_buf, format="PNG")
    img_bytes = img_buf.getvalue()

    # 5. Submit Translation Job
    files = {"file": ("test_xray.png", img_bytes, "image/png")}
    data = {"model_version": "v1"}

    inf_res = client.post("/api/v1/inference", files=files, data=data, headers=headers)
    assert inf_res.status_code == 200
    inf_data = inf_res.json()
    assert inf_data["success"] is True
    job_result = inf_data["data"]

    job_id = job_result["id"]
    assert job_result["status"] == "COMPLETED"
    assert job_result["output_image_url"] is not None
    assert job_result["processing_time_ms"] > 0
    assert "NOT a clinical CT scan" in job_result["disclaimer"]

    # 6. Retrieve specific job by ID
    get_res = client.get(f"/api/v1/inference/{job_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == job_id

    # 7. Check History
    hist_res = client.get("/api/v1/inference/history", headers=headers)
    assert hist_res.status_code == 200
    hist_items = hist_res.json()["data"]["items"]
    assert any(item["id"] == job_id for item in hist_items)
