
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4


from app.modules.shared.enums import ProjectStatus, ProjectVisibility
from app.modules.shared.root_aggregate import AggregateRoot
from app.modules.projects.domain.events.project_events import (
     ProjectArchivedEvent,
     ProjectCreatedEvent,
     ProjectDeletedEvent, 
     ProjectRenamedEvent, 
     ProjectDescriptionUpdatedEvent,
     ProjectRestoredEvent,
     ProjectVisibilityChangedEvent,
     SoftwareAttachedToProjectEvent,
     SoftwareDetachedFromProjectEvent,
     )
from app.modules.projects.domain.exceptions import (
     InvalidProjectDescriptionError, 
     InvalidProjectNameError,
     InvalidProjectStateError, 
     ProjectArchivedError, 
     ProjectDeletedError,
     )

def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)

@dataclass(slots=True)
class Project(AggregateRoot):
    """Represents a software project.
       A `Project` is the top-level container for packages owned by a creator.

       The aggregate is responsible for:
           - Project metadata
           - Lifecycle
           - Visibility
           - Ownership
           - Accepting new software
    """
    id: UUID
    owner_id: UUID

    name: str
    description: str

    visibility: ProjectVisibility = ProjectVisibility.PUBLIC
    status: ProjectStatus = ProjectStatus.ACTIVE

    created_at: datetime
    updated_at: datetime

    deleted_at: datetime
    deleted_by: datetime

    def __post_init__(self) -> None:
            self.created_at = _ensure_utc(self.created_at)
            self.updated_at = _ensure_utc(self.updated_at)

    def utc_now() -> datetime:
        return datetime.now(timezone.utc)
        
    
    @classmethod
    def create(
        cls,
        *,
        owner_id: UUID,
        name: str,
        description: str,
        visibility: ProjectVisibility = ProjectVisibility.PRIVATE,
    ) -> "Project":
        v_name = cls._validate_name(name)
        v_description = cls._validate_description(description)
        now = cls.utc_now()
        project = cls(
                         id=uuid4(),
                         owner_id=owner_id,
                         name=v_name,
                         description=v_description,
                         visibility=visibility,
                         status=ProjectStatus.ACTIVE,
                         created_at=now,
                         deleted_at=None,
                         deleted_by=None,
                    )
        # Record event
        project._record_event(
             ProjectCreatedEvent(
                  agregate_id=project.id,
                  actor_id=project.owner_id,
             )
        )
        return project


   
    @property
    def is_active(self) -> bool:
         return self is ProjectStatus.ACTIVE

    @property
    def is_archived(self) -> bool:
         return self is ProjectStatus.ARCHIVED

    @property
    def is_deleted(self) -> bool:
         return self is ProjectStatus.DELETED


    @staticmethod
    def _validate_name(name: str) -> str:
         """Validate and normalize a project name."""
         normalized = name.strip()
         if not normalized:
              raise InvalidProjectNameError(
                   "Project name cannot be empty."
              )
         if len(normalized) > 120:
              raise InvalidProjectNameError(
                   "Project name cannot exceed 120 characters."
              )
         if any(ord(ch) < 32 for ch in normalized):
              raise InvalidProjectNameError(
                   "Project name cannot contain invalid characters."
              )
         return normalized

    @staticmethod
    def _validate_description(description: str) -> str:
         """Validate and normalize a project description."""

         normalized = (description or "").strip()

         if len(normalized) > 5000:
              raise InvalidProjectDescriptionError(
                   """Project description cannot exceed 5000 characters."""
              )
         invalid = {
              ch
              for ch in normalized
              if ord(ch) < 32 and ch not in ("\n", "\r", "\t")
         }

         if invalid:
              raise InvalidProjectDescriptionError(
                   "Project description contains invalid control characters."
              )
         return normalized

    def rename(self, name: str) -> None:
         """Rename a project."""

         self._ensure_modifiable()

         normalized = self._validate_name(name)
         if normalized == self.name:
              return

         self.name = normalized
         self._touch()

         # Record event.
         self._record_event(
              ProjectRenamedEvent(
                   actor_id=self.owner_id,
                   agregate_id=self.id,
                   old_name=self.name,
                   new_name=name,
              )
         )

    def update_description(
              self,
              *,
              description: str | None,
    ):
         """Update project description."""
         self._ensure_modifiable()
         normalized = self._validate_description(description)

         if normalized == self.description:
              return

         old_description = self.description
         self.description = normalized

         self._touch()
         # Record event
         self._record_event(
              ProjectDescriptionUpdatedEvent(
                   agregate_id=self.id,
                   actor_id=self.owner_id,
                   old_description=old_description,
                   new_description=normalized,
              ),
         )

    def archive(self) -> None:
         """Archive a project."""

         self._ensure_not_deleted()

         if not self.status.can_archive:
              raise InvalidProjectStateError(
                   """Only active projects can be archived."""
              )

         self.status = ProjectStatus.ARCHIVED
         self._touch()
          
         self._record_event(
              ProjectArchivedEvent(
                   agregate_id=self.id,
                   actor_id=self.owner_id,
              )
         )
         
    def change_visibilitY(
              self,
              *,
              visibility: ProjectVisibility,
              ) -> None:
         """Change project visibility."""
         self._ensure_modifiable()
         if visibility is self.visibility:
              return

         old_visibility = self.visibility
         self.visibility = visibility

         self._touch()

         self._record_event(
              ProjectVisibilityChangedEvent(
                   aggregate_id=self.id,
                   actor_id=self.owner_id,
                   old_visibility=old_visibility,
                   new_visibility=self.visibility,
              )
         )

    def restore(self) -> None:
         """Restore an archived project."""
         self._ensure_not_deleted()
         if self.status is not ProjectStatus.ARCHIVED:
              raise InvalidProjectStateError(
                   """Only archived project can be restored."""
              )
         self.status = ProjectStatus.ACTIVE
         self._touch()

         self._record_event(
              ProjectRestoredEvent(
                   agregate_id=self.id,
                   actor_id=self.owner_id,
              )
         )

    def mark_deleted(
              self,
              *,
              deleted_by: UUID,
              ) -> None:
         """Soft delete software."""
         self._ensure_not_deleted()

         now = self.utc_now()

         self.status = ProjectStatus.DELETED
         self.deleted_at = now
         self.deleted_by = deleted_by
         self.updated_at = now

         # Record deletion event
         self._record_event(
              ProjectDeletedEvent(
                   agregate_id=self.id,
                   actor_id=self.owner_id,
                   deleted_by=deleted_by,
                   deleted_at=now,
              )
         )

    def ensure_can_accept_software(self) -> None:
         """check if a project can have a software."""
         if self.status == ProjectStatus.ACTIVE:
              return

         REJECTED_STATUSES = (ProjectStatus.ARCHIVED, ProjectStatus.DELETED)
         if self.status in REJECTED_STATUSES:
              raise InvalidProjectStateError(
                   """Project cannot accept new software currently."""
              )
              
    def attach_software(
              self,
              *,
              software_id: UUID,
    ) -> None:
         """Attach a software to a project."""
         self._ensure_can_accept_software()

         self._record_event(
              SoftwareAttachedToProjectEvent(
                   agregate_id=self.id,
                   actor_id=self.owner_id,
                   software_id=software_id,
              )
         )

    def dettach_software(
              self,
              *,
              software_id: UUID,
    ) -> None:
         """Detach a software from a project."""
         self._ensure_modifiable()
         self._record_event(
              SoftwareDetachedFromProjectEvent(
                   agregate_id=self.id,
                   actor_id=self.owner_id,
                   software_id=software_id
              )
         )



    # === HELPERS ===
    def _ensure_not_deleted(self) -> None:
         """Ensure project is not deleted."""
         if self.status is ProjectStatus.DELETED:
                       raise ProjectDeletedError(
                            "Project already deleted."
                       )
         
    def  _ensure_modifiable(self) -> None:
         """Ensure the project can be modifiable."""

         self._ensure_not_deleted()

    def _touch(self) -> None:
         self.updated_at = self.utc_now()

    def _ensure_can_accept_software(self) -> None:
         """Ensure software can be added to the project."""

         self._ensure_not_deleted()

         if self.status is ProjectStatus.ARCHIVED:
              raise ProjectArchivedError(
                   "Archived projects cannot accept new software."
              )
