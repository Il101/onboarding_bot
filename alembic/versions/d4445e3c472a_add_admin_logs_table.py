"""add_admin_logs_table

Revision ID: d4445e3c472a
Revises: f9520363ecac
Create Date: 2026-05-01 11:08:38.760205

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4445e3c472a'
down_revision: Union[str, Sequence[str], None] = 'f9520363ecac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "admin_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("admin_id", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("target_type", sa.String(length=50), nullable=False),
        sa.Column("target_id", sa.String(length=100), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_admin_logs_admin_id"), "admin_logs", ["admin_id"], unique=False)
    op.create_index(op.f("ix_admin_logs_created_at"), "admin_logs", ["created_at"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_admin_logs_created_at"), table_name="admin_logs")
    op.drop_index(op.f("ix_admin_logs_admin_id"), table_name="admin_logs")
    op.drop_table("admin_logs")
