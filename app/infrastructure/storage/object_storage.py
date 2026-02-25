from __future__ import annotations

from typing import AsyncIterator

from app.infrastructure.storage.base import StorageBackend


class ObjectStorageBackend(StorageBackend):
    """
    Placeholder for object storage adapters (S3, GCS, MinIO).
    Implementations should stream chunks and avoid buffering whole objects.
    """

    async def init_upload(self, upload_id: str) -> None:
        raise NotImplementedError

    async def append_upload_chunk(self, upload_id: str, chunk: bytes) -> None:
        raise NotImplementedError

    async def get_upload_size(self, upload_id: str) -> int:
        raise NotImplementedError

    async def stream_upload(
        self,
        upload_id: str,
        *,
        start: int = 0,
        end: int | None = None,
        chunk_size: int = 1024 * 1024,
    ) -> AsyncIterator[bytes]:
        raise NotImplementedError

    async def abort_upload(self, upload_id: str) -> None:
        raise NotImplementedError

    async def promote_upload(self, upload_id: str, storage_key: str) -> bool:
        raise NotImplementedError

    async def stream_object(
        self,
        storage_key: str,
        *,
        start: int = 0,
        end: int | None = None,
        chunk_size: int = 1024 * 1024,
    ) -> AsyncIterator[bytes]:
        raise NotImplementedError

    async def get_object_size(self, storage_key: str) -> int:
        raise NotImplementedError

    async def delete_object(self, storage_key: str) -> None:
        raise NotImplementedError
