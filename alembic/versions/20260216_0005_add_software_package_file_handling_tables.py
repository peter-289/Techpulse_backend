"""add software package file handling tables

Revision ID: 20260216_0005
Revises: 20260216_0004
Create Date: 2026-02-16 01:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260216_0005"
down_revision: Union[str, None] = "20260216_0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "software_packages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("is_public", sa.Boolean(), nullable=False),
        sa.Column("latest_version", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_software_packages_owner_name"),
    )
    op.create_index(op.f("ix_software_packages_id"), "software_packages", ["id"], unique=False)
    op.create_index(op.f("ix_software_packages_owner_id"), "software_packages", ["owner_id"], unique=False)
    op.create_index(op.f("ix_software_packages_name"), "software_packages", ["name"], unique=False)

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
    op.create_index(op.f("ix_file_blobs_id"), "file_blobs", ["id"], unique=False)
    op.create_index(op.f("ix_file_blobs_checksum_sha256"), "file_blobs", ["checksum_sha256"], unique=False)

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
    op.create_index(op.f("ix_file_versions_id"), "file_versions", ["id"], unique=False)
    op.create_index(op.f("ix_file_versions_package_id"), "file_versions", ["package_id"], unique=False)
    op.create_index(op.f("ix_file_versions_blob_id"), "file_versions", ["blob_id"], unique=False)
    op.create_index(op.f("ix_file_versions_checksum_sha256"), "file_versions", ["checksum_sha256"], unique=False)

    op.create_table(
        "upload_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("package_name", sa.String(length=150), nullable=False),
        sa.Column("package_description", sa.Text(), nullable=False),
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
    op.create_index(op.f("ix_upload_sessions_user_id"), "upload_sessions", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_upload_sessions_user_id"), table_name="upload_sessions")
    op.drop_table("upload_sessions")

    op.drop_index(op.f("ix_file_versions_checksum_sha256"), table_name="file_versions")
    op.drop_index(op.f("ix_file_versions_blob_id"), table_name="file_versions")
    op.drop_index(op.f("ix_file_versions_package_id"), table_name="file_versions")
    op.drop_index(op.f("ix_file_versions_id"), table_name="file_versions")
    op.drop_table("file_versions")

    op.drop_index(op.f("ix_file_blobs_checksum_sha256"), table_name="file_blobs")
    op.drop_index(op.f("ix_file_blobs_id"), table_name="file_blobs")
    op.drop_table("file_blobs")

    op.drop_index(op.f("ix_software_packages_name"), table_name="software_packages")
    op.drop_index(op.f("ix_software_packages_owner_id"), table_name="software_packages")
    op.drop_index(op.f("ix_software_packages_id"), table_name="software_packages")
    op.drop_table("software_packages")
