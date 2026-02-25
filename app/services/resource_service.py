from app.core.unit_of_work import UnitOfWork
from app.exceptions.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.resource import Resource
from app.schemas.resource import ResourceCreate


class ResourceService:
    ALLOWED_TYPES = {"api", "knowledge", "support", "updates"}

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    def list_resources(self, type_filter: str | None = None) -> list[Resource]:
        normalized = type_filter.strip().lower() if type_filter else None
        with self.uow:
            return self.uow.resource_repo.list_resources(type_filter=normalized)

    def get_by_slug(self, slug: str) -> Resource:
        with self.uow:
            resource = self.uow.resource_repo.get_by_slug(slug=slug)
            if not resource:
                raise NotFoundError("Resource not found")
            return resource

    def create_resource(self, payload: ResourceCreate) -> Resource:
        if payload.type.lower() not in self.ALLOWED_TYPES:
            raise ValidationError(f"Invalid resource type. Allowed: {', '.join(sorted(self.ALLOWED_TYPES))}")
        with self.uow:
            existing = self.uow.resource_repo.get_by_slug(slug=payload.slug)
            if existing:
                raise ConflictError("Resource slug already exists")
            resource = Resource(
                title=payload.title.strip(),
                slug=payload.slug.strip().lower(),
                type=payload.type.strip().lower(),
                description=payload.description.strip(),
                url=(payload.url or "").strip() or None,
            )
            return self.uow.resource_repo.add(resource)

    def delete_resource(self, slug: str) -> None:
        with self.uow:
            resource = self.uow.resource_repo.get_by_slug(slug=slug)
            if not resource:
                raise NotFoundError("Resource not found")
            self.uow.resource_repo.delete(resource)

