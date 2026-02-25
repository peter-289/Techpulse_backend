from typing import Optional

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepo:
    def __init__(self, db: Session):
        self.db = db

    def add(self, project: Project) -> Project:
        self.db.add(project)
        self.db.flush()
        self.db.refresh(project)
        return project

    def get_by_id(self, project_id: int) -> Optional[Project]:
        return self.db.get(Project, project_id)

    def list_visible_for_user(self, user_id: int, cursor: int | None = None, limit: int = 50) -> list[Project]:
        stmt = (
            select(Project)
            .where(or_(Project.is_public.is_(True), Project.user_id == user_id))
            .order_by(Project.id.desc())
            .limit(limit)
        )
        if cursor is not None:
            stmt = stmt.where(Project.id < cursor)
        return self.db.execute(stmt).scalars().all()

    def increment_download_count(self, project_id: int) -> None:
        stmt = (
            update(Project)
            .where(Project.id == project_id)
            .values(download_count=Project.download_count + 1)
        )
        self.db.execute(stmt)

    def delete(self, project: Project) -> None:
        self.db.delete(project)
