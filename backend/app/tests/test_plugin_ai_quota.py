from __future__ import annotations

import asyncio

import pytest

from app.services import plugin_ai_quota


class _FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}
        self.hashes: dict[str, dict[str, int]] = {}
        self.zsets: dict[str, dict[str, int]] = {}
        self.lock = asyncio.Lock()

    async def ping(self) -> bool:
        return True

    async def eval(self, script: str, numkeys: int, *args):
        keys = list(args[:numkeys])
        argv = list(args[numkeys:])
        async with self.lock:
            if "minute_used" in script:
                minute_key, minute_amount_key, daily_key = keys
                estimate, per_minute, daily = map(int, argv[:3])
                now_ms = int(argv[5])
                window_ms = int(argv[6])
                reservation_id = str(argv[7])
                zset = self.zsets.setdefault(minute_key, {})
                amounts = self.hashes.setdefault(minute_amount_key, {})
                for rid, score in list(zset.items()):
                    if score <= now_ms - window_ms:
                        zset.pop(rid, None)
                        amounts.pop(rid, None)
                minute_used = sum(amounts.get(rid, 0) for rid in zset)
                daily_used = self.values.get(daily_key, 0)
                if per_minute > 0 and minute_used + estimate > per_minute:
                    return [0, "per_minute", minute_used, per_minute]
                if daily > 0 and daily_used + estimate > daily:
                    return [0, "daily", daily_used, daily]
                zset[reservation_id] = now_ms
                amounts[reservation_id] = estimate
                self.values[minute_key] = minute_used + estimate
                self.values[daily_key] = daily_used + estimate
                return [1, "ok", self.values[minute_key], self.values[daily_key]]

            delta = int(argv[0])
            reservation_id = str(argv[1])
            minute_key, minute_amount_key, daily_key = keys
            current = self.hashes.setdefault(minute_amount_key, {}).get(reservation_id)
            if current is not None:
                next_amount = current + delta
                if next_amount <= 0:
                    self.hashes[minute_amount_key].pop(reservation_id, None)
                    self.zsets.setdefault(minute_key, {}).pop(reservation_id, None)
                else:
                    self.hashes[minute_amount_key][reservation_id] = next_amount
                self.values[minute_key] = sum(
                    self.hashes[minute_amount_key].get(rid, 0)
                    for rid in self.zsets.setdefault(minute_key, {})
                )
            if daily_key in self.values:
                self.values[daily_key] = max(0, self.values.get(daily_key, 0) + delta)
            return [1]


@pytest.mark.asyncio
async def test_acquire_uses_redis_pre_reservation_for_concurrent_limit(monkeypatch) -> None:
    fake = _FakeRedis()

    async def _limits(_plugin_key: str):
        return {"per_minute": 100, "daily": 1000}

    async def _noop_usage(*_args, **_kwargs) -> None:
        return None

    monkeypatch.setattr(plugin_ai_quota, "get_redis", lambda: fake)
    monkeypatch.setattr(plugin_ai_quota, "_load_quota_limits", _limits)
    monkeypatch.setattr(plugin_ai_quota, "_write_quota_error_usage", _noop_usage)

    results = await asyncio.gather(
        plugin_ai_quota.acquire("demo", 7, 60),
        plugin_ai_quota.acquire("demo", 7, 60),
        return_exceptions=True,
    )

    tickets = [item for item in results if isinstance(item, plugin_ai_quota.PluginAIQuotaTicket)]
    errors = [item for item in results if isinstance(item, plugin_ai_quota.PluginAIQuotaExceeded)]
    assert len(tickets) == 1
    assert len(errors) == 1
    assert tickets[0].backend == "redis"

    await plugin_ai_quota.release(tickets[0], actual_tokens=20)
    assert fake.values[tickets[0].minute_key] == 20
    assert fake.values[tickets[0].daily_key] == 20


@pytest.mark.asyncio
async def test_acquire_allows_when_quota_disabled(monkeypatch) -> None:
    async def _limits(_plugin_key: str):
        return {"per_minute": 0, "daily": 0}

    monkeypatch.setattr(plugin_ai_quota, "_load_quota_limits", _limits)

    ticket = await plugin_ai_quota.acquire("demo", 7, 999999)

    assert ticket.limited is False
    assert ticket.backend == "disabled"
    assert ticket.minute_key is None
