from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .value_objects import VersionNumber


@dataclass(frozen=True, slots=True)
class SoftwareUploaded:
    software_id: UUID
    version_id: UUID
    artifact_id: UUID
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class VersionPublished:
    software_id: UUID
    version_id: UUID
    version: VersionNumber
    occurred_at: datetime

