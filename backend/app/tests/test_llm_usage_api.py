from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from app.api.llm_usage import list_plugin_llm_usage_summary


@dataclass
class _Row:
    source: str
    request_count: int
    success_count: int
    input_tokens: int
    output_tokens: int
    avg_latency_ms: float
    last_used_at: datetime


class _Result:
    def __init__(self, rows: list[_Row]) -> None:
        self._rows = rows

    def all(self) -> list[_Row]:
        return self._rows


class _DB:
    async def execute(self, _stmt):
        return _Result(
            [
                _Row(
                    source="plugin:demo",
                    request_count=3,
                    success_count=2,
                    input_tokens=10,
                    output_tokens=5,
                    avg_latency_ms=12.7,
                    last_used_at=datetime(2026, 5, 27, tzinfo=UTC),
                )
            ]
        )


@pytest.mark.asyncio
async def test_list_plugin_llm_usage_summary_shapes_rows() -> None:
    resp = await list_plugin_llm_usage_summary(_DB(), object(), plugin_key=None, limit=50)

    assert len(resp.items) == 1
    item = resp.items[0]
    assert item.plugin_key == "demo"
    assert item.source == "plugin:demo"
    assert item.request_count == 3
    assert item.success_count == 2
    assert item.failed_count == 1
    assert item.total_tokens == 15
    assert item.avg_latency_ms == 12
