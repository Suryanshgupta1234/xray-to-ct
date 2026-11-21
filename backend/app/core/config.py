"""
Application Settings & Configuration Management.
Uses Pydantic Settings for strict environment variable parsing and validation.
"""

from pathlib import Path
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Core Application Settings
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PROJECT_NAME: str = "X-Ray to CT Image Translation API"
    API_PREFIX: str = "/api/v1"

    # Security & JWT Authentication
    JWT_SECRET: str = "super_secret_dev_key_change_me_in_production_min_32_characters_12345"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database Configuration (PostgreSQL with SQLite fallback)
    DATABASE_URL: str = "sqlite+aiosqlite:///./xray_ct.db"
    DATABASE_URL_SYNC: str = "sqlite:///./xray_ct.db"

    # Storage Settings
    STORAGE_TYPE: str = "local"  # "local", "s3", or "minio"
    LOCAL_STORAGE_PATH: str = "./storage"
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "xray-ct-storage"
    S3_REGION: str = "us-east-1"

    # Redis Cache (Optional in dev)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Machine Learning Settings
    MODEL_DIR: str = "../models"
    ACTIVE_MODEL_VERSION: str = "v1"
    ACTIVE_MODEL_PATH: str = "../models/v1/generator.pth"
    DEVICE: str = "auto"
    IMAGE_SIZE: int = 256

    # File Upload Constraints
    MAX_UPLOAD_SIZE_MB: int = 25
    ALLOWED_EXTENSIONS: str = "png,jpg,jpeg,dcm"
    ALLOWED_MIME_TYPES: str = "image/png,image/jpeg,application/dicom,application/octet-stream"

    # CORS Configuration
    CORS_ORIGINS: str = (
        "https://xray-to-ct.vercel.app,"
        "https://xray-to-ct.onrender.com,"
        "http://localhost:5173,"
        "http://localhost:3000,"
        "http://127.0.0.1:5173,"
        "http://127.0.0.1:3000"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        origins = [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]
        # Explicitly guarantee production and local origins
        required_origins = [
            "https://xray-to-ct.vercel.app",
            "https://xray-to-ct.onrender.com",
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
        ]
        for req in required_origins:
            if req not in origins:
                origins.append(req)
        return origins

    @property
    def allowed_extensions_list(self) -> List[str]:
        return [ext.strip().lower() for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


settings = Settings()
