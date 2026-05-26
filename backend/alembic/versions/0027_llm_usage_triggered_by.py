"""add triggered_by_account_id to llm_usage

Revision ID: 0027
Revises: 0026
Create Date: 2026-05-27
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("llm_usage", sa.Column("triggered_by_account_id", sa.Integer(), nullable=True))
    op.create_index(
        "ix_llm_usage_triggered_by_account_id",
        "llm_usage",
        ["triggered_by_account_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_llm_usage_triggered_by_account_id", table_name="llm_usage")
    op.drop_column("llm_usage", "triggered_by_account_id")
