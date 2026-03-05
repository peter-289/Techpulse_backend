"""sms cutover tables

Revision ID: 20260304_0007
Revises: 20260216_0006
Create Date: 2026-03-04 22:40:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260304_0007"
down_revision: Union[str, None] = "20260216_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    if _table_exists("upload_sessions"):
        op.drop_table("upload_sessions")
    if _table_exists("file_versions"):
        op.drop_table("file_versions")
    if _table_exists("file_blobs"):
        op.drop_table("file_blobs")
    if _table_exists("software_packages"):
        op.drop_table("software_packages")

    op.create_table(
        "sms_softwares",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("row_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_sms_software_owner_name"),
    )
    op.create_index("ix_sms_softwares_owner_id", "sms_softwares", ["owner_id"], unique=False)
    op.create_index("ix_sms_softwares_created_at", "sms_softwares", ["created_at"], unique=False)

    op.create_table(
        "sms_artifacts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
    )
    op.create_index("ix_sms_artifacts_file_hash", "sms_artifacts", ["file_hash"], unique=False)
    op.create_index("ix_sms_artifacts_created_at", "sms_artifacts", ["created_at"], unique=False)

    op.create_table(
        "sms_versions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("software_id", sa.Uuid(), nullable=False),
        sa.Column("artifact_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["artifact_id"], ["sms_artifacts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["software_id"], ["sms_softwares.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artifact_id"),
        sa.UniqueConstraint("software_id", "version", name="uq_sms_versions_software_version"),
    )
    op.create_index("ix_sms_versions_software_id", "sms_versions", ["software_id"], unique=False)
    op.create_index("ix_sms_versions_created_at", "sms_versions", ["created_at"], unique=False)
    op.create_index(
        "ix_sms_versions_software_id_version",
        "sms_versions",
        ["software_id", "version"],
        unique=False,
    )


def downgrade() -> None:
    if _table_exists("sms_versions"):
        op.drop_table("sms_versions")
    if _table_exists("sms_artifacts"):
        op.drop_table("sms_artifacts")
    if _table_exists("sms_softwares"):
        op.drop_table("sms_softwares")

    op.create_table(
        "software_packages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("language", sa.String(length=80), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("latest_version", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_software_packages_owner_name"),
    )
    op.create_index("ix_software_packages_id", "software_packages", ["id"], unique=False)
    op.create_index("ix_software_packages_owner_id", "software_packages", ["owner_id"], unique=False)
    op.create_index("ix_software_packages_name", "software_packages", ["name"], unique=False)
    op.create_index("ix_software_packages_category", "software_packages", ["category"], unique=False)
    op.create_index("ix_software_packages_language", "software_packages", ["language"], unique=False)

    op.create_table(
        "file_blobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(length=600), nullable=False),
        sa.Column("reference_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key"),
        sa.UniqueConstraint("checksum_sha256", "size_bytes", name="uq_file_blobs_checksum_size"),
    )
    op.create_index("ix_file_blobs_id", "file_blobs", ["id"], unique=False)
    op.create_index("ix_file_blobs_checksum_sha256", "file_blobs", ["checksum_sha256"], unique=False)

    op.create_table(
        "file_versions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("package_id", sa.Integer(), nullable=False),
        sa.Column("blob_id", sa.Integer(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["blob_id"], ["file_blobs.id"]),
        sa.ForeignKeyConstraint(["package_id"], ["software_packages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("package_id", "version", name="uq_file_versions_package_version"),
    )
    op.create_index("ix_file_versions_id", "file_versions", ["id"], unique=False)
    op.create_index("ix_file_versions_package_id", "file_versions", ["package_id"], unique=False)
    op.create_index("ix_file_versions_blob_id", "file_versions", ["blob_id"], unique=False)
    op.create_index("ix_file_versions_checksum_sha256", "file_versions", ["checksum_sha256"], unique=False)

    op.create_table(
        "upload_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("package_name", sa.String(length=150), nullable=False),
        sa.Column("package_description", sa.Text(), nullable=False),
        sa.Column("package_category", sa.String(length=80), nullable=False),
        sa.Column("package_language", sa.String(length=80), nullable=False),
        sa.Column("package_version", sa.String(length=64), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("bytes_received", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_size_bytes", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="PENDING"),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("completed_file_version_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["completed_file_version_id"], ["file_versions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_upload_sessions_user_id", "upload_sessions", ["user_id"], unique=False)

