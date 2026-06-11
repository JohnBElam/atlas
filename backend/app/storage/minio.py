from __future__ import annotations

import re
from functools import lru_cache
from uuid import UUID

import boto3
from botocore.client import BaseClient

from app.config import settings

_SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(filename: str) -> str:
    """Strip path separators, control chars; enforce safe charset."""
    base = filename.replace("\\", "/").split("/")[-1]
    base = "".join(ch for ch in base if ord(ch) >= 32)
    safe = _SAFE_FILENAME_RE.sub("_", base).strip("._")
    if not safe:
        raise ValueError("Filename is empty after sanitization")
    return safe


def upload_prefix(source_id: UUID) -> str:
    return f"uploads/{source_id}/"


class MinioStorage:
    def __init__(self) -> None:
        self._client: BaseClient = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            aws_access_key_id=settings.minio_access_key,
            aws_secret_access_key=settings.minio_secret_key,
            region_name="us-east-1",
        )
        self.bucket = settings.minio_bucket_data

    def list_filenames(self, source_id: UUID) -> list[str]:
        prefix = upload_prefix(source_id)
        filenames: list[str] = []
        continuation: str | None = None
        while True:
            kwargs: dict = {"Bucket": self.bucket, "Prefix": prefix}
            if continuation:
                kwargs["ContinuationToken"] = continuation
            response = self._client.list_objects_v2(**kwargs)
            for item in response.get("Contents", []):
                key = item["Key"]
                if key == prefix or key.endswith("/"):
                    continue
                filenames.append(key[len(prefix) :])
            if not response.get("IsTruncated"):
                break
            continuation = response.get("NextContinuationToken")
        return sorted(filenames)

    def upload_file(self, source_id: UUID, filename: str, data: bytes) -> str:
        safe_name = sanitize_filename(filename)
        key = f"{upload_prefix(source_id)}{safe_name}"
        self._client.put_object(Bucket=self.bucket, Key=key, Body=data)
        return safe_name

    def download_file(self, source_id: UUID, filename: str) -> bytes:
        key = f"{upload_prefix(source_id)}{filename}"
        response = self._client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()


@lru_cache
def get_minio_storage() -> MinioStorage:
    return MinioStorage()
