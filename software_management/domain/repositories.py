from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .aggregates import Software


class SoftwareRepositoryProtocol(Protocol):
    async def get_software(self, software_id: UUID) -> Software | None:
        ...

