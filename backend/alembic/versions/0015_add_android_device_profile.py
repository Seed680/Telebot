"""add Android device profile

Revision ID: 0015
Revises: 0014
Create Date: 2026-05-07

添加安卓设备伪装配置：Samsung Galaxy S24 / Android 14 / Telegram 12.6.4
"""

from __future__ import annotations

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO device_profile
            (name, device_model, system_version, app_version, lang_code, system_lang_code, is_default)
        VALUES
            ('Android Telegram', 'Samsung Galaxy S24', 'Android 14', 'Telegram 12.6.4', 'zh-hans', 'zh-Hans', false);
        """
    )


def downgrade() -> None:
    op.execute("DELETE FROM device_profile WHERE name = 'Android Telegram';")
