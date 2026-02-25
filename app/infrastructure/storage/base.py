from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator


class StorageBackend(ABC):
    """Abstraction for binary object storage used by package uploads/downloads."""

    @abstractmethod
    async def init_upload(self, upload_id: str) -> None:
        """Initialize temporary upload target."""

    @abstractmethod
    async def append_upload_chunk(self, upload_id: str, chunk: bytes) -> None:
        """Append bytes to an in-progress upload."""

    @abstractmethod
    async def get_upload_size(self, upload_id: str) -> int:
        """Return bytes currently written for an in-progress upload."""

    @abstractmethod
    async def stream_upload(
        self,
        upload_id: str,
        *,
        start: int = 0,
        end: int | None = None,
        chunk_size: int = 1024 * 1024,
    ) -> AsyncIterator[bytes]:
        """Stream an in-progress upload."""

    @abstractmethod
    async def abort_upload(self, upload_id: str) -> None:
        """Abort and clean up temporary upload data."""

    @abstractmethod
    async def promote_upload(self, upload_id: str, storage_key: str) -> bool:
        """
        Move temp upload to a permanent key.
        Returns True if newly stored, False if key already existed and temp upload was discarded.
        """

    @abstractmethod
    async def stream_object(
        self,
        storage_key: str,
        *,
        start: int = 0,
        end: int | None = None,
        chunk_size: int = 1024 * 1024,
    ) -> AsyncIterator[bytes]:
        """Stream an object for download."""

    @abstractmethod
    async def get_object_size(self, storage_key: str) -> int:
        """Return stored object size."""

    @abstractmethod
    async def delete_object(self, storage_key: str) -> None:
        """Delete object by key."""
