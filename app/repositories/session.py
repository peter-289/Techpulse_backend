from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.models.session import UserSession


class SessionRepo:
    def __init__(self, db: Session):
        self.db = db

    def add_session(self, session: UserSession) -> UserSession:
        self.db.add(session)
        self.db.flush()
        self.db.refresh(session)
        return session

    def get_by_refresh_hash(self, refresh_hash: str) -> Optional[UserSession]:
        stmt = select(UserSession).where(UserSession.refresh_token_hash == refresh_hash)
        return self.db.execute(stmt).scalar_one_or_none()

    def revoke_session(self, session: UserSession, revoked_at: datetime) -> None:
        session.revoked_at = revoked_at

    def revoke_user_sessions(self, user_id: int, revoked_at: datetime) -> None:
        stmt = (
            update(UserSession)
            .where(UserSession.user_id == user_id)
            .where(UserSession.revoked_at.is_(None))
            .values(revoked_at=revoked_at)
        )
        self.db.execute(stmt)
