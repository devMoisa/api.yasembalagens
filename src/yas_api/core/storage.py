"""Cliente de armazenamento para Digital Ocean Spaces (S3-compativel)."""

from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

import boto3
from botocore.config import Config

from yas_api.core.config import settings


@dataclass(frozen=True)
class StoredObject:
    key: str
    public_url: str


class ObjectStorage(Protocol):
    def upload(self, *, key: str, content: bytes, content_type: str) -> StoredObject: ...
    def delete(self, *, key: str) -> None: ...
    def public_url(self, key: str) -> str: ...


class SpacesStorage:
    def __init__(
        self,
        *,
        region: str,
        bucket: str,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        public_base_url: str,
    ) -> None:
        if not bucket:
            raise RuntimeError("YAS_SPACES_BUCKET nao configurado")
        if not access_key or not secret_key:
            raise RuntimeError("Credenciais do Spaces nao configuradas")
        self._bucket = bucket
        self._public_base_url = public_base_url.rstrip("/")
        self._client = boto3.client(
            "s3",
            region_name=region,
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
        )

    def upload(self, *, key: str, content: bytes, content_type: str) -> StoredObject:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
            ACL="public-read",
            CacheControl="public, max-age=31536000, immutable",
        )
        return StoredObject(key=key, public_url=self.public_url(key))

    def delete(self, *, key: str) -> None:
        self._client.delete_object(Bucket=self._bucket, Key=key)

    def public_url(self, key: str) -> str:
        return f"{self._public_base_url}/{key.lstrip('/')}"


@lru_cache
def get_storage() -> ObjectStorage:
    return SpacesStorage(
        region=settings.spaces_region,
        bucket=settings.spaces_bucket,
        access_key=settings.spaces_access_key,
        secret_key=settings.spaces_secret_key,
        endpoint_url=settings.resolved_spaces_endpoint,
        public_base_url=settings.resolved_spaces_public_base,
    )
