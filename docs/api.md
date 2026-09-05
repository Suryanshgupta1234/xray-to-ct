# REST API Reference & Integration Guide

The **X-Ray to CT Translation API** provides an asynchronous, authenticated REST interface for submitting planar radiographs, inspecting model metadata, and querying historical translation jobs.

All API responses are wrapped in a standard JSON envelope:

```json
{
  "success": true,
  "data": { ... },
  "message": "Operation completed successfully"
}
```

On client or server errors:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_IMAGE",
    "message": "File header does not match any allowed medical image format."
  }
}
```

---

## 1. Authentication Endpoints

### Register Account
`POST /api/v1/auth/register`

- **Request Body**:
  ```json
  {
    "email": "researcher@lab.edu",
    "password": "SecurePassword123!",
    "full_name": "Dr. Jane Doe"
  }
  ```
- **Response**: `201 Created`
  ```json
  {
    "success": true,
    "data": {
      "access_token": "eyJhbGciOiJIUzI1NiIs...",
      "token_type": "bearer",
      "user": {
        "id": "c62b7194-e0c1-4ba2-bca4-d13eb194b633",
        "email": "researcher@lab.edu",
        "full_name": "Dr. Jane Doe",
        "role": "USER",
        "is_active": true,
        "created_at": "2026-09-05T14:30:00Z"
      }
    },
    "message": "Account created successfully"
  }
  ```

### Log In
`POST /api/v1/auth/login`

- **Request Body**:
  ```json
  {
    "email": "researcher@lab.edu",
    "password": "SecurePassword123!"
  }
  ```
- **Response**: `200 OK` (Returns JWT access token)

### Get Current User Profile
`GET /api/v1/auth/me`
- **Headers**: `Authorization: Bearer <access_token>`

---

## 2. Inference Endpoints

### Submit 2D X-Ray for Translation
`POST /api/v1/inference`

- **Headers**:
  - `Authorization: Bearer <access_token>`
  - `Content-Type: multipart/form-data`
- **Form Data**:
  - `file`: Raw binary image file (`.png`, `.jpg`, `.jpeg`, `.dcm`)
  - `model_version` *(optional)*: e.g., `"v1"`
- **Response**: `200 OK`
  ```json
  {
    "success": true,
    "data": {
      "id": "8f8c2b51-7f9a-41f2-8924-a7d18e8f85f1",
      "user_id": "c62b7194-e0c1-4ba2-bca4-d13eb194b633",
      "status": "COMPLETED",
      "model_version": "v1",
      "original_filename": "chest_xray_pa.png",
      "image_format": "image/png",
      "input_image_url": "/api/v1/images/uploads/8f8c2b51.png",
      "output_image_url": "/api/v1/images/results/a391e4fc.png",
      "difference_map_url": "/api/v1/images/results/d410b3fa.png",
      "processing_time_ms": 38.4,
      "created_at": "2026-09-05T14:35:10Z",
      "completed_at": "2026-09-05T14:35:10.038400Z",
      "disclaimer": "RESEARCH ONLY: Generated image is an AI statistical approximation and is NOT a clinical CT scan. Must NOT be used for clinical diagnosis, treatment decisions, or patient care."
    },
    "message": "X-Ray to CT translation generated successfully"
  }
  ```

### Get Inference Job
`GET /api/v1/inference/{id}`

### List Translation History
`GET /api/v1/inference/history?page=1&page_size=10`

### Delete Inference Job
`DELETE /api/v1/inference/{id}`

---

## 3. System Health & Models

### System Health
`GET /api/v1/health`

- **Response**: `200 OK`
  ```json
  {
    "success": true,
    "data": {
      "status": "healthy",
      "version": "1.0.0",
      "device": "cpu",
      "api": { "status": "healthy" },
      "database": { "status": "healthy" },
      "storage": { "status": "healthy" },
      "model_cache": {
        "status": "healthy",
        "details": {
          "cached_versions": ["v1"],
          "active_version": "v1",
          "device": "cpu",
          "cuda_available": false
        }
      }
    }
  }
  ```

### List Model Versions
`GET /api/v1/models`

### Administrative Telemetry
`GET /api/v1/models/admin/stats`
*(Requires ADMIN role)*
