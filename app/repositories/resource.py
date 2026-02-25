from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.resource import Resource


class ResourceRepo:
    def __init__(self, db: Session):
        self.db = db

    def add(self, resource: Resource) -> Resource:
        self.db.add(resource)
        self.db.flush()
        self.db.refresh(resource)
        return resource

    def get_by_slug(self, slug: str) -> Optional[Resource]:
        stmt = select(Resource).where(Resource.slug == slug)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_resources(self, type_filter: str | None = None) -> list[Resource]:
        stmt = select(Resource).order_by(Resource.created_at.desc())
        if type_filter:
            stmt = stmt.where(Resource.type == type_filter)
        return self.db.execute(stmt).scalars().all()

    def delete(self, resource: Resource) -> None:
        self.db.delete(resource)

