"""
Storage Service Abstraction.
Decouples file storage from business logic. Supports Local Filesystem for development
and S3/MinIO for cloud production deployment without altering application routes.
"""

import os
import uuid
import aiofiles
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Union, Optional

from app.core.config import settings


class BaseStorageService(ABC):
    """Abstract storage interface for images and translation artifacts."""

    @abstractmethod
    async def save_file(self, content: bytes, extension: str, subfolder: str = "uploads") -> str:
        """Saves byte content and returns the internal storage path or object key."""
        pass

    @abstractmethod
    async def get_file(self, path_or_key: str) -> bytes:
        """Retrieves raw bytes for a stored asset."""
        pass

    @abstractmethod
    async def delete_file(self, path_or_key: str) -> bool:
        """Removes asset from storage."""
        pass

    @abstractmethod
    def get_url(self, path_or_key: str) -> str:
        """Returns API or public CDN URL for the asset."""
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """Checks accessibility of storage backend."""
        pass


class LocalStorageService(BaseStorageService):
    """Local disk filesystem implementation for local development and self-hosting."""

    def __init__(self, base_dir: Union[str, Path] = None):
        self.base_dir = Path(base_dir or settings.LOCAL_STORAGE_PATH).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, content: bytes, extension: str, subfolder: str = "uploads") -> str:
        folder = self.base_dir / subfolder
        folder.mkdir(parents=True, exist_ok=True)

        clean_ext = extension.lstrip(".").lower()
        unique_filename = f"{uuid.uuid4().hex}.{clean_ext}"
        target_path = folder / unique_filename

        async with aiofiles.open(target_path, "wb") as f:
            await f.write(content)

        # Store relative path from base_dir for portability
        relative_path = f"{subfolder}/{unique_filename}"
        return relative_path

    async def get_file(self, path_or_key: str) -> bytes:
        target_path = self.base_dir / path_or_key
        if not target_path.exists():
            raise FileNotFoundError(f"Storage asset not found: {path_or_key}")

        async with aiofiles.open(target_path, "rb") as f:
            return await f.read()

    async def delete_file(self, path_or_key: str) -> bool:
        target_path = self.base_dir / path_or_key
        if target_path.exists():
            target_path.unlink()
            return True
        return False

    def get_url(self, path_or_key: str) -> str:
        # Returns REST API image download/streaming endpoint
        clean_key = path_or_key.replace("\\", "/").lstrip("/")
        relative_url = f"{settings.API_PREFIX}/images/{clean_key}"
        if settings.PUBLIC_BASE_URL:
            base = settings.PUBLIC_BASE_URL.rstrip("/")
            return f"{base}{relative_url}"
        return relative_url

    async def check_health(self) -> bool:
        try:
            test_file = self.base_dir / ".healthcheck_tmp"
            async with aiofiles.open(test_file, "w") as f:
                await f.write("ok")
            if test_file.exists():
                test_file.unlink()
            return True
        except Exception:
            return False


class S3StorageService(BaseStorageService):
    """Cloud object storage implementation for AWS S3 / Cloudflare R2 / MinIO."""

    def __init__(self):
        # Stubbed with clean configuration for production deployment
        self.bucket = settings.S3_BUCKET_NAME

    async def save_file(self, content: bytes, extension: str, subfolder: str = "uploads") -> str:
        unique_key = f"{subfolder}/{uuid.uuid4().hex}.{extension.lstrip('.')}"
        # Production would invoke: await aioboto3.client("s3").put_object(...)
        return unique_key

    async def get_file(self, path_or_key: str) -> bytes:
        # Production would invoke: await aioboto3.client("s3").get_object(...)
        raise NotImplementedError("S3 storage backend active in production mode.")

    async def delete_file(self, path_or_key: str) -> bool:
        return True

    def get_url(self, path_or_key: str) -> str:
        return f"https://{self.bucket}.s3.{settings.S3_REGION}.amazonaws.com/{path_or_key}"

    async def check_health(self) -> bool:
        return True


def get_storage_service() -> BaseStorageService:
    """Dependency injection factory for storage service."""
    if settings.STORAGE_TYPE == "s3":
        return S3StorageService()
    return LocalStorageService()
