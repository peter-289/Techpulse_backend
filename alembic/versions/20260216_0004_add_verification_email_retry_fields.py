"""add verification email retry tracking fields to users

Revision ID: 20260216_0004
Revises: 20260213_0003
Create Date: 2026-02-16 00:00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260216_0004"
down_revision: Union[str, None] = "20260213_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("verification_email_last_sent_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("verification_email_retry_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("verification_email_next_retry_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("verification_email_last_error", sa.String(length=500), nullable=True))
    op.create_index(
        op.f("ix_users_verification_email_next_retry_at"),
        "users",
        ["verification_email_next_retry_at"],
        unique=False,
    )
    # SQLite does not support direct ALTER COLUMN operations; batch mode keeps
    # this migration portable across SQLite (dev) and Postgres (prod).
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("verification_email_retry_count", server_default=None)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_verification_email_next_retry_at"), table_name="users")
    op.drop_column("users", "verification_email_last_error")
    op.drop_column("users", "verification_email_next_retry_at")
    op.drop_column("users", "verification_email_retry_count")
    op.drop_column("users", "verification_email_last_sent_at")
