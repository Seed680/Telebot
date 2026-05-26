"""create plugin_global_config table

Revision ID: 0028
Revises: 0027
Create Date: 2026-05-27
"""

from __future__ import annotations

from typing import Any

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import context, op

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def _copy_manifest(manifest: Any) -> dict[str, Any]:
    if isinstance(manifest, dict):
        return dict(manifest)
    return {}


def upgrade() -> None:
    op.create_table(
        "plugin_global_config",
        sa.Column(
            "plugin_key",
            sa.String(),
            sa.ForeignKey("feature.key", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "config",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    if context.is_offline_mode():
        return

    bind = op.get_bind()
    feature = sa.table(
        "feature",
        sa.column("key", sa.String()),
        sa.column("manifest", sa.JSON()),
    )
    plugin_global_config = sa.table(
        "plugin_global_config",
        sa.column("plugin_key", sa.String()),
        sa.column("config", postgresql.JSONB(astext_type=sa.Text())),
    )

    rows = bind.execute(sa.select(feature.c.key, feature.c.manifest)).all()
    for key, manifest in rows:
        legacy_config = _copy_manifest(manifest).get("global_config")
        if not isinstance(legacy_config, dict):
            continue
        bind.execute(
            plugin_global_config.insert().values(
                plugin_key=key,
                config=legacy_config,
            )
        )


def downgrade() -> None:
    if context.is_offline_mode():
        op.drop_table("plugin_global_config")
        return

    bind = op.get_bind()
    feature = sa.table(
        "feature",
        sa.column("key", sa.String()),
        sa.column("manifest", sa.JSON()),
    )
    plugin_global_config = sa.table(
        "plugin_global_config",
        sa.column("plugin_key", sa.String()),
        sa.column("config", postgresql.JSONB(astext_type=sa.Text())),
    )

    rows = bind.execute(
        sa.select(plugin_global_config.c.plugin_key, plugin_global_config.c.config)
    ).all()
    for plugin_key, config in rows:
        feature_row = bind.execute(
            sa.select(feature.c.manifest).where(feature.c.key == plugin_key)
        ).first()
        if feature_row is None:
            continue
        manifest = _copy_manifest(feature_row.manifest)
        manifest["global_config"] = dict(config or {})
        bind.execute(
            feature.update()
            .where(feature.c.key == plugin_key)
            .values(manifest=manifest)
        )

    op.drop_table("plugin_global_config")
