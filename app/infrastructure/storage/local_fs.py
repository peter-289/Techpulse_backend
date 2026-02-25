from __future__ import annotations

from pathlib import Path
from typing import AsyncIterator

import anyio

from app.infrastructure.storage.base import StorageBackend


class LocalFileSystemStorage(StorageBackend):
    """Local FS storage backend with temp + permanent object namespaces."""

    def __init__(self, root: Path):
        self.root = root
        self.temp_root = self.root / "tmp"
        self.object_root = self.root / "objects"
        self.temp_root.mkdir(parents=True, exist_ok=True)
        self.object_root.mkdir(parents=True, exist_ok=True)

    def _temp_path(self, upload_id: str) -> Path:
        return self.temp_root / f"{upload_id}.part"

    def _object_path(self, storage_key: str) -> Path:
        normalized = Path(storage_key)
        if normalized.is_absolute() or ".." in normalized.parts:
            raise ValueError("Invalid storage key")
        return self.object_root / normalized

    async def init_upload(self, upload_id: str) -> None:
        path = self._temp_path(upload_id)

        def _init() -> None:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb"):
                return

        await anyio.to_thread.run_sync(_init)

    async def append_upload_chunk(self, upload_id: str, chunk: bytes) -> None:
        path = self._temp_path(upload_id)

        def _append() -> None:
            with path.open("ab") as handle:
                handle.write(chunk)

        await anyio.to_thread.run_sync(_append)

    async def get_upload_size(self, upload_id: str) -> int:
        path = self._temp_path(upload_id)
        return await anyio.to_thread.run_sync(lambda: path.stat().st_size if path.exists() else 0)

    async def stream_upload(
        self,
        upload_id: str,
        *,
        start: int = 0,
        end: int | None = None,
        chunk_size: int = 1024 * 1024,
    ) -> AsyncIterator[bytes]:
        path = self._temp_path(upload_id)
        handle = await anyio.to_thread.run_sync(lambda: path.open("rb"))
        try:
            await anyio.to_thread.run_sync(handle.seek, start)
            remaining = None if end is None else (end - start + 1)
            while True:
                to_read = chunk_size if remaining is None else min(chunk_size, remaining)
                if to_read <= 0:
                    break
                data = await anyio.to_thread.run_sync(handle.read, to_read)
                if not data:
                    break
                if remaining is not None:
                    remaining -= len(data)
                yield data
        finally:
            await anyio.to_thread.run_sync(handle.close)

    async def abort_upload(self, upload_id: str) -> None:
        path = self._temp_path(upload_id)
        await anyio.to_thread.run_sync(lambda: path.unlink(missing_ok=True))

    async def promote_upload(self, upload_id: str, storage_key: str) -> bool:
        src = self._temp_path(upload_id)
        dst = self._object_path(storage_key)

        def _promote() -> bool:
            if not src.exists():
                raise FileNotFoundError(f"Upload temp file not found: {src}")
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                src.unlink(missing_ok=True)
                return False
            src.replace(dst)
            return True

        return await anyio.to_thread.run_sync(_promote)

    async def stream_object(
        self,
        storage_key: str,
        *,
        start: int = 0,
        end: int | None = None,
        chunk_size: int = 1024 * 1024,
    ) -> AsyncIterator[bytes]:
        path = self._object_path(storage_key)
        handle = await anyio.to_thread.run_sync(lambda: path.open("rb"))
        try:
            await anyio.to_thread.run_sync(handle.seek, start)
            remaining = None if end is None else (end - start + 1)
            while True:
                to_read = chunk_size if remaining is None else min(chunk_size, remaining)
                if to_read <= 0:
                    break
                data = await anyio.to_thread.run_sync(handle.read, to_read)
                if not data:
                    break
                if remaining is not None:
                    remaining -= len(data)
                yield data
        finally:
            await anyio.to_thread.run_sync(handle.close)

    async def get_object_size(self, storage_key: str) -> int:
        path = self._object_path(storage_key)
        return await anyio.to_thread.run_sync(lambda: path.stat().st_size)

    async def delete_object(self, storage_key: str) -> None:
        path = self._object_path(storage_key)
        await anyio.to_thread.run_sync(lambda: path.unlink(missing_ok=True))
