import hashlib
from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass
class StoredEvidence:
    bucket_name: str
    storage_key: str
    sha256_hex: str
    byte_size: int
    mime_type: str


class StorageClient:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.headers = {
            "Authorization": f"Bearer {self.settings.service_role_key}",
            "apikey": self.settings.service_role_key,
        }

    def ensure_bucket(self) -> None:
        lookup = httpx.get(
            f"{self.settings.storage_internal_url}/bucket/{self.settings.storage_bucket}",
            headers=self.headers,
            timeout=10,
        )
        if lookup.status_code == 200:
            return
        if lookup.status_code != 404 and not self._is_bucket_not_found(lookup):
            lookup.raise_for_status()

        payload = {
            "id": self.settings.storage_bucket,
            "name": self.settings.storage_bucket,
            "public": False,
            "file_size_limit": 52428800,
            "allowed_mime_types": ["image/jpeg", "image/png", "image/webp"],
        }
        response = httpx.post(
            f"{self.settings.storage_internal_url}/bucket",
            headers=self.headers,
            json=payload,
            timeout=10,
        )
        if response.status_code in (200, 201, 409) or self._is_bucket_already_exists(response):
            return
        response.raise_for_status()

    @staticmethod
    def _is_bucket_already_exists(response: httpx.Response) -> bool:
        if response.status_code != 400:
            return False
        try:
            payload = response.json()
        except ValueError:
            return False
        if payload.get("code") == "BucketAlreadyExists":
            return True
        nested = payload.get("originalError")
        return isinstance(nested, dict) and nested.get("code") == "BucketAlreadyExists"

    @staticmethod
    def _is_bucket_not_found(response: httpx.Response) -> bool:
        if response.status_code not in (400, 404):
            return False
        try:
            payload = response.json()
        except ValueError:
            return False
        if payload.get("statusCode") in ("404", 404):
            return True
        if payload.get("code") == "BucketNotFound":
            return True
        return payload.get("error") == "Bucket not found"

    def upload(self, *, object_path: str, content: bytes, content_type: str) -> StoredEvidence:
        digest = hashlib.sha256(content).hexdigest()
        response = httpx.post(
            f"{self.settings.storage_internal_url}/object/{self.settings.storage_bucket}/{object_path}",
            headers={**self.headers, "content-type": content_type, "x-upsert": "true"},
            content=content,
            timeout=30,
        )
        response.raise_for_status()
        return StoredEvidence(
            bucket_name=self.settings.storage_bucket,
            storage_key=object_path,
            sha256_hex=digest,
            byte_size=len(content),
            mime_type=content_type,
        )

    def download(self, *, bucket_name: str, object_path: str) -> tuple[bytes, str]:
        response = httpx.get(
            f"{self.settings.storage_internal_url}/object/{bucket_name}/{object_path}",
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.content, response.headers.get("content-type", "application/octet-stream")

    def status(self) -> bool:
        response = httpx.get(f"{self.settings.storage_internal_url}/status", timeout=5)
        return response.status_code == 200
