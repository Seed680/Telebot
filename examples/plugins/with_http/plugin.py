"""受控 HTTP facade 示例模块。"""

from __future__ import annotations

from typing import Any

from app.worker.plugins.base import Plugin, PluginContext, register

DEFAULT_URL = "https://api.github.com/zen"


async def http_status_handler(
    client: Any,
    event: Any,
    args: list[str],
    account_id: int,
    ctx: PluginContext,
) -> None:
    """Fetch one allow-listed URL through ctx.http and edit the command message."""

    if ctx.http is None:
        await event.edit("ctx.http 未初始化：请确认 manifest 声明 external_http 和 allowed_hosts。")
        return

    url = (args[0] if args else ctx.config.get("url") or DEFAULT_URL).strip()
    response = await ctx.http.get(url)
    preview = response.text.strip().replace("\n", " ")[:120]
    await event.edit(f"HTTP {response.status_code}: {preview}")


@register
class WithHTTPPlugin(Plugin):
    key = "with_http"
    display_name = "HTTP 示例"
    commands = {"http_status": http_status_handler}
    owner_only = True


__all__ = ["WithHTTPPlugin", "http_status_handler"]
