from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db_setup import Base


class UploadSession(Base):
    __tablename__ = "upload_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    package_name: Mapped[str] = mapped_column(String(150), nullable=False)
    package_description: Mapped[str] = mapped_column(Text, nullable=False)
    package_category: Mapped[str] = mapped_column(String(80), nullable=False)
    package_language: Mapped[str] = mapped_column(String(80), nullable=False)
    package_version: Mapped[str] = mapped_column(String(64), nullable=False)
    is_public: Mapped[bool] = mapped_column(nullable=False, default=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bytes_received: Mapped[int] = mapped_column(nullable=False, default=0)
    max_size_bytes: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="PENDING")
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    completed_file_version_id: Mapped[int | None] = mapped_column(ForeignKey("file_versions.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
