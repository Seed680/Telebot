"""Shared pytest compatibility helpers."""

from __future__ import annotations

from unittest import mock

import pytest

if not hasattr(pytest, "mock"):
    pytest.mock = mock  # type: ignore[attr-defined]
