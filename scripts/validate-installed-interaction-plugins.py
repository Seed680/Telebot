#!/usr/bin/env python3
"""Validate installed interaction plugin metadata stays in sync with MANIFEST."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = ROOT / "backend"
INSTALLED_ROOT = ROOT / "plugins" / "installed"

for import_root in (ROOT, BACKEND_ROOT):
    path = str(import_root)
    if path not in sys.path:
        sys.path.insert(0, path)

from app.worker.plugins.manifest import Manifest  # noqa: E402

REQUIRED_FILES = {"plugin.json", "manifest.py", "plugin.py", "__init__.py"}


def _load_installed_module(plugin_key: str, filename: str) -> types.ModuleType:
    package_root = "plugins.installed"
    if package_root not in sys.modules:
        pkg = types.ModuleType(package_root)
        pkg.__path__ = [str(INSTALLED_ROOT)]  # type: ignore[attr-defined]
        sys.modules[package_root] = pkg

    package_name = f"{package_root}.{plugin_key}"
    plugin_dir = INSTALLED_ROOT / plugin_key
    if package_name not in sys.modules:
        pkg = types.ModuleType(package_name)
        pkg.__path__ = [str(plugin_dir)]  # type: ignore[attr-defined]
        sys.modules[package_name] = pkg

    path = plugin_dir / filename
    module_name = f"{package_name}.{filename[:-3]}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise AssertionError(f"{plugin_key}: 无法加载模块 {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _load_plugin_json(plugin_dir: Path) -> dict[str, Any]:
    path = plugin_dir / "plugin.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{path}: plugin.json 不是合法 JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise AssertionError(f"{path}: plugin.json 顶层必须是 object")
    return data


def _installed_interaction_plugin_keys() -> list[str]:
    keys: set[str] = set()
    for plugin_dir in sorted(path for path in INSTALLED_ROOT.iterdir() if path.is_dir()):
        plugin_json = plugin_dir / "plugin.json"
        manifest_py = plugin_dir / "manifest.py"
        has_interaction_entries = False
        if plugin_json.is_file():
            metadata = _load_plugin_json(plugin_dir)
            entries = metadata.get("interaction_entries")
            has_interaction_entries = isinstance(entries, list) and any(isinstance(item, dict) for item in entries)
        if not has_interaction_entries and manifest_py.is_file():
            manifest_module = _load_installed_module(plugin_dir.name, "manifest.py")
            manifest = getattr(manifest_module, "MANIFEST", None)
            has_interaction_entries = isinstance(manifest, Manifest) and any(
                isinstance(item, dict) for item in manifest.interaction_entries
            )
        if has_interaction_entries:
            keys.add(plugin_dir.name)
    return sorted(keys)


def _validate_plugin(plugin_key: str) -> None:
    plugin_dir = INSTALLED_ROOT / plugin_key
    missing = sorted(file for file in REQUIRED_FILES if not (plugin_dir / file).is_file())
    if missing:
        raise AssertionError(f"{plugin_key}: 缺少必要文件: {', '.join(missing)}")

    metadata = _load_plugin_json(plugin_dir)
    manifest_module = _load_installed_module(plugin_key, "manifest.py")
    manifest = getattr(manifest_module, "MANIFEST", None)
    if not isinstance(manifest, Manifest):
        raise AssertionError(f"{plugin_key}: MANIFEST 必须是 Manifest 实例")

    plugin_json_key = metadata.get("name") or metadata.get("key")
    if plugin_json_key != manifest.key:
        raise AssertionError(f"{plugin_key}: plugin.json key 与 MANIFEST.key 不一致")
    if metadata.get("version") != manifest.version:
        raise AssertionError(f"{plugin_key}: plugin.json.version 与 MANIFEST.version 不一致")
    if metadata.get("category") != manifest.category:
        raise AssertionError(f"{plugin_key}: plugin.json.category 与 MANIFEST.category 不一致")
    if metadata.get("interaction_profile") != manifest.interaction_profile:
        raise AssertionError(f"{plugin_key}: plugin.json.interaction_profile 与 MANIFEST.interaction_profile 不一致")
    if list(metadata.get("interaction_entries") or []) != list(manifest.interaction_entries):
        raise AssertionError(f"{plugin_key}: plugin.json.interaction_entries 与 MANIFEST.interaction_entries 不一致")

    print(f"ok: {plugin_key}")


def main() -> int:
    if not INSTALLED_ROOT.is_dir():
        raise AssertionError(f"已安装插件目录不存在: {INSTALLED_ROOT}")

    plugin_keys = _installed_interaction_plugin_keys()
    if not plugin_keys:
        raise AssertionError("未发现声明 interaction_entries 的已安装插件")

    for plugin_key in plugin_keys:
        _validate_plugin(plugin_key)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AssertionError as exc:
        print(f"installed interaction plugin validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
