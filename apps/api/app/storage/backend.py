"""File storage abstraction layer: defaults to local storage, extensible to S3/OSS/MinIO."""

from __future__ import annotations

import os
import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import settings

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "pdf", "mp4", "mov"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


class StorageBackend:
    def save(self, file: UploadFile, subdir: str = "") -> tuple[str, str, int, str]:
        raise NotImplementedError

    def url_for(self, path: str) -> str:
        raise NotImplementedError


class LocalStorage(StorageBackend):
    def __init__(self) -> None:
        self.base_dir = Path(settings.STORAGE_LOCAL_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, file: UploadFile, subdir: str = "") -> tuple[str, str, int, str]:
        ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {ext}")
        data = file.file.read()
        if len(data) > MAX_FILE_SIZE:
            raise ValueError("File size exceeds limit (20MB)")
        sub = Path(subdir) if subdir else Path("")
        target_dir = self.base_dir / sub
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}.{ext}"
        full_path = target_dir / filename
        full_path.write_bytes(data)
        rel_path = str(sub / filename) if subdir else filename
        url = f"/api/v1/files/{rel_path.replace(os.sep, '/')}"
        return rel_path, url, len(data), ext

    def abs_path(self, rel_path: str) -> Path:
        return self.base_dir / rel_path

    def url_for(self, rel_path: str) -> str:
        return f"/api/v1/files/{rel_path.replace(os.sep, '/')}"


_backend: StorageBackend | None = None


def get_storage() -> StorageBackend:
    global _backend
    if _backend is None:
        if settings.STORAGE_TYPE == "s3" and settings.S3_BUCKET:
            _backend = _S3StoragePlaceholder()
        else:
            _backend = LocalStorage()
    return _backend


class _S3StoragePlaceholder(StorageBackend):
    """S3 placeholder implementation: reserved for future use, actual upload not implemented."""

    def save(self, file: UploadFile, subdir: str = "") -> tuple[str, str, int, str]:
        raise NotImplementedError("S3 storage not implemented in MVP, please use local storage")

    def url_for(self, path: str) -> str:
        raise NotImplementedError
