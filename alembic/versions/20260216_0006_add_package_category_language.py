"""add package category and language metadata

Revision ID: 20260216_0006
Revises: 20260216_0005
Create Date: 2026-02-16 03:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260216_0006"
down_revision: Union[str, None] = "20260216_0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("software_packages", sa.Column("category", sa.String(length=80), nullable=True))
    op.add_column("software_packages", sa.Column("language", sa.String(length=80), nullable=True))
    op.execute("UPDATE software_packages SET category='student projects' WHERE category IS NULL")
    op.execute("UPDATE software_packages SET language='Unknown' WHERE language IS NULL")
    # Use batch mode for SQLite compatibility (ALTER COLUMN unsupported).
    with op.batch_alter_table("software_packages") as batch_op:
        batch_op.alter_column("category", nullable=False)
        batch_op.alter_column("language", nullable=False)
    op.create_index(op.f("ix_software_packages_category"), "software_packages", ["category"], unique=False)
    op.create_index(op.f("ix_software_packages_language"), "software_packages", ["language"], unique=False)

    op.add_column("upload_sessions", sa.Column("package_category", sa.String(length=80), nullable=True))
    op.add_column("upload_sessions", sa.Column("package_language", sa.String(length=80), nullable=True))
    op.execute("UPDATE upload_sessions SET package_category='student projects' WHERE package_category IS NULL")
    op.execute("UPDATE upload_sessions SET package_language='Unknown' WHERE package_language IS NULL")
    with op.batch_alter_table("upload_sessions") as batch_op:
        batch_op.alter_column("package_category", nullable=False)
        batch_op.alter_column("package_language", nullable=False)


def downgrade() -> None:
    op.drop_column("upload_sessions", "package_language")
    op.drop_column("upload_sessions", "package_category")
    op.drop_index(op.f("ix_software_packages_language"), table_name="software_packages")
    op.drop_index(op.f("ix_software_packages_category"), table_name="software_packages")
    op.drop_column("software_packages", "language")
    op.drop_column("software_packages", "category")
