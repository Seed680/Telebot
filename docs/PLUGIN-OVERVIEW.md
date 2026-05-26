# TelePilot 模块概览

本文保留旧版开发指南中“路线、快速开始、模块结构”的原文内容。

## 插件市场路线：Route A vs Route B

TelePilot 插件市场分两条路线推进，0.x 阶段明确选择 **Route A**：

- **Route A：受信/签名模块市场。** 仅接收 TelePilot/Anoyou 审核过的模块源，安装包需要签名或可信来源记录，模块在同一 worker 进程内运行，通过 `Manifest.permissions`、`ctx.client`、`ctx.http`、`ctx.ai` 等 facade 收口能力。它适合 0.x 快速稳定迭代，把重点放在模块 API、安装体验、权限声明、审计日志和回滚能力上。
- **Route B：开放社区市场。** 面向任意第三方上传或未经人工审核的模块，需要 subprocess/容器隔离、资源配额、文件系统/网络沙箱、供应链扫描和更完整的安全策略。它不属于 0.x 默认方案，若 1.0 之后开放社区市场，应作为独立 Epic 设计和验收。

因此，本文当前所有示例、CI 和安全边界都按 Route A 编写；不要把 Route A 的 facade 误读为零信任沙箱。

---

## 1. 快速开始

### 文件结构

```
plugins/installed/{模块名}/
├── __init__.py        # 导出 PLUGIN_CLASS 和 MANIFEST
├── manifest.py        # Manifest 元数据
├── plugin.py          # 模块主类
└── (其他模块)
```

### 最小可运行模块

**plugin.py：**
```python
from app.worker.plugins.base import Plugin, register

@register
class PingPlugin(Plugin):
    key = "ping"
    display_name = "Ping"

    async def on_command(self, ctx, cmd, args, event) -> bool:
        if cmd == "ping":
            await event.edit("pong")
            return True
        return False
```

**manifest.py：**
```python
from app.worker.plugins.manifest import Manifest

MANIFEST = Manifest(
    key="ping",
    display_name="Ping",
    version="0.1.0",
    author="example",
    description="响应 ping 指令",
    permissions=["edit_message"],
)
```

**__init__.py：**
```python
from .manifest import MANIFEST
from .plugin import PingPlugin

PLUGIN_CLASS = PingPlugin
__all__ = ["PLUGIN_CLASS", "MANIFEST"]
```

通过安装接口安装并在账号上启用后，worker 会在授权检查通过时加载它。仅手工拷贝到 `plugins/installed/ping/` 的目录会被标记为孤立目录（orphan）并拒绝加载。

---

## 2. 模块结构（Plugin 包）

### 目录约定

```
backend/app/worker/plugins/
├── base.py              # Plugin 基类 + register 装饰器
├── manifest.py          # Manifest 数据类
├── loader.py            # 模块加载器 + 热重载 + generation guard
└── builtin/             # 内置模块
    ├── game24/
    └── forward/

plugins/installed/       # 远程/用户安装的模块
├── guess_number/
└── (更多模块...)
```

### 生命周期

```
loader._load_all()
  → scan builtin/ + plugins/installed/
  → import plugin.py + manifest.py
  → 验证 Manifest 合法性
  → 实例化 Plugin 子类
  → 调用 on_startup(ctx)

热重载 (reload_plugin):
  → state.generation += 1          # generation guard
  → 旧模块: on_shutdown(ctx)
  → 重新 import + 实例化
  → 新模块: on_startup(ctx)

消息派发:
  → 检查 ctx.generation == state.generation
  → 跳过过期 handler（竞态保护）
  → 调用 on_command / on_message
```

---
