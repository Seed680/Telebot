"""add unified installed_plugin table

Revision ID: 0026
Revises: 0025
Create Date: 2026-05-27

Additive first step toward consolidating plugin_install and remote_plugin.
Runtime code still reads the legacy tables in this release; this table exists
so a later minor can backfill, dual-write, then switch loader reads safely.
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0026"
down_revision = "0025"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "installed_plugin",
        sa.Column("key", sa.String(length=128), primary_key=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("installed_path", sa.Text(), nullable=True),
        sa.Column("version", sa.String(length=64), nullable=False, server_default="0.0.0"),
        sa.Column("manifest_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("signature_ok", sa.Boolean(), nullable=True),
        sa.Column("trust_tier", sa.String(length=32), nullable=False, server_default="community"),
        sa.Column("source_label", sa.String(length=64), nullable=True),
        sa.Column("last_install_error", sa.Text(), nullable=True),
        sa.Column("last_load_error", sa.Text(), nullable=True),
        sa.Column(
            "lint_warnings",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("installed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_installed_plugin_source", "installed_plugin", ["source"])
    op.create_index("ix_installed_plugin_enabled", "installed_plugin", ["enabled"])
    op.create_index("ix_installed_plugin_trust_tier", "installed_plugin", ["trust_tier"])


def downgrade() -> None:
    op.drop_index("ix_installed_plugin_trust_tier", table_name="installed_plugin")
    op.drop_index("ix_installed_plugin_enabled", table_name="installed_plugin")
    op.drop_index("ix_installed_plugin_source", table_name="installed_plugin")
    op.drop_table("installed_plugin")
