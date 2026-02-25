from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.db_setup import Base


class FileBlob(Base):
    __tablename__ = "file_blobs"
    __table_args__ = (
        UniqueConstraint("checksum_sha256", "size_bytes", name="uq_file_blobs_checksum_size"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, index=True)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    storage_key: Mapped[str] = mapped_column(String(600), nullable=False, unique=True)
    reference_count: Mapped[int] = mapped_column(nullable=False, default=1)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
