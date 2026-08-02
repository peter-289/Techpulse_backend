from __future__ import annotations


from dataclasses import dataclass
from datetime import datetime
from uuid import UUID
from app.modules.shared.events import DomainEvent

@dataclass(frozen=True, slots=True)
class ProjectCreatedEvent(DomainEvent):
    """Represents a project created event after a project has been created."""


@dataclass(frozen=True, slots=True)
class ProjectRenamedEvent(DomainEvent):
    """Represents a project renamed event."""
    old_name: str
    new_name: str

@dataclass(frozen=True, slots=True)
class ProjectDescriptionUpdatedEvent(DomainEvent):
    """Represents a description update event."""
    old_description: str
    new_description: str | None

@dataclass(frozen=True, slots=True)
class ProjectArchivedEvent(DomainEvent):
    """Represents a project archived event."""    

@dataclass(frozen=True, slots=True)
class ProjectRestoredEvent(DomainEvent):
    """Project restored event."""

@dataclass(frozen=True, slots=True)
class ProjectDeletedEvent(DomainEvent):
    """Project deleted event."""
    deleted_by: UUID
    deleted_at: datetime

@dataclass(frozen=True, slots=True)
class ProjectVisibilityChangedEvent(DomainEvent):
    """Project visibility changed event."""
    old_visibility: str
    new_visibility: str

@dataclass(frozen=True, slots=True)
class SoftwareAttachedToProjectEvent(DomainEvent):
    software_id: UUID

@dataclass(frozen=True, slots=True)
class SoftwareDetachedFromProjectEvent(DomainEvent):
    software_id: UUID