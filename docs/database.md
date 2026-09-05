# Database Architecture & Entity Relationships

The data layer is built on **SQLAlchemy 2.0 Async ORM**, offering dual-engine portability:
- **PostgreSQL 16** with `asyncpg` for multi-worker containerized production.
- **SQLite 3** with `aiosqlite` for zero-configuration, self-contained local testing.

---

## 1. Entity-Relationship Diagram

```mermaid
erDiagram
    USERS ||--o{ INFERENCE_JOBS : "executes"
    MODEL_VERSIONS ||--o{ INFERENCE_JOBS : "references"

    USERS {
        string id PK "UUID v4"
        string email UK "Unique indexed email"
        string hashed_password "Bcrypt hash"
        string full_name "Display name"
        string role "USER or ADMIN"
        boolean is_active "Account status"
        timestamp created_at "UTC creation timestamp"
        timestamp updated_at "UTC update timestamp"
    }

    INFERENCE_JOBS {
        string id PK "UUID v4"
        string user_id FK "References USERS(id)"
        string input_image_path "Storage path of raw X-Ray"
        string output_image_path "Storage path of synthetic CT"
        string original_filename "Uploaded client filename"
        string image_format "PNG, JPEG, or DICOM"
        string model_version "References model version e.g. v1"
        string status "PENDING, PROCESSING, COMPLETED, FAILED"
        float processing_time_ms "Pure forward latency in ms"
        text error_message "Failure detail if errored"
        json metadata_json "Windowing, shapes, and difference map paths"
        timestamp created_at "UTC creation timestamp"
        timestamp completed_at "UTC completion timestamp"
    }

    MODEL_VERSIONS {
        string id PK "UUID v4"
        string version UK "Unique identifier e.g. v1"
        string model_name "pix2pix_unet256"
        string architecture "UNet256_PatchGAN"
        string weights_path "Filesystem or S3 weight location"
        boolean is_active "Active runtime flag"
        json hyperparameters "Batch size, lr, lambda"
        json evaluation_metrics "MAE, MSE, PSNR, SSIM"
        timestamp created_at "UTC registration timestamp"
    }
```

---

## 2. Indexing Strategy & Query Optimization

| Table | Column | Index Type | Optimization Goal |
| :--- | :--- | :--- | :--- |
| `users` | `email` | `UNIQUE B-Tree` | $O(1)$ fast lookup during login authentication without full table scan. |
| `inference_jobs` | `user_id` | `B-Tree` | Accelerates paginated user history queries (`WHERE user_id = ? ORDER BY created_at DESC`). |
| `inference_jobs` | `status` | `B-Tree` | Optimizes admin telemetry queries counting completed vs failed jobs. |
| `inference_jobs` | `created_at` | `B-Tree (Desc)` | Fast chronological pagination and cursor sorting. |
| `model_versions` | `version` | `UNIQUE B-Tree` | Ensures zero ambiguity during model loading and caching. |

---

## 3. Data Integrity & Cascade Rules

1. **User Deletion**:
   - `ondelete="CASCADE"` is configured on `InferenceJob.user_id`. When a user account is deleted, associated job records are automatically pruned.
2. **Password Security**:
   - Plaintext passwords are never persisted. Passwords are encrypted using `bcrypt` with adaptive salt rounds before database submission.
3. **PHI De-identification**:
   - DICOM records strip all HIPAA identifiers (names, MRNs, dates of birth) prior to storing metadata in `metadata_json`.
