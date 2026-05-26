# TelePilot 插件示例

本目录用于放置可维护的第三方模块示例。CI 只校验已经迁移到稳定公开 API 的示例，避免把历史写法或未合并接口误判为推荐模板。

## 当前推荐

- `with_http`：最小 HTTP facade 示例，演示 `manifest.py` 如何声明 `external_http`、`allowed_hosts`，以及运行时如何通过 `ctx.http` 发起受控请求。
- `with_ai`：最小 AI facade 示例，演示 `manifest.py` 如何声明 `ai_text`，以及运行时如何通过 `ctx.ai.complete` / `ctx.ai.list_providers` 使用平台统一 LLM 池。

## 暂不纳入 CI 的示例

- `translate`：历史示例，仍直接复用后端私有 LLM 链路。它保留作迁移参考，但不是新的第三方模块模板。
