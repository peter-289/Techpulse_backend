from __future__ import annotations

import hashlib
from typing import AsyncIterable


class StreamingSHA256:
    """Incremental SHA-256 helper used during chunked uploads."""

    def __init__(self):
        self._hasher = hashlib.sha256()
        self._size_bytes = 0

    @property
    def size_bytes(self) -> int:
        return self._size_bytes

    def update(self, chunk: bytes) -> None:
        if not chunk:
            return
        self._hasher.update(chunk)
        self._size_bytes += len(chunk)

    def hexdigest(self) -> str:
        return self._hasher.hexdigest()


async def hash_stream(stream: AsyncIterable[bytes]) -> tuple[str, int]:
    hasher = StreamingSHA256()
    async for chunk in stream:
        hasher.update(chunk)
    return hasher.hexdigest(), hasher.size_bytes
