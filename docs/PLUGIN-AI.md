# TelePilot 插件 AI facade

`ctx.ai` 已作为第三方模块可用的受控文本 AI facade。模块需要在 `plugin.json` 和 `manifest.py` 中声明 `permissions=["ai_text"]`，运行时才会注入 `ctx.ai`。

## 推荐写法

```python
if ctx.ai is None:
    await event.edit("本模块需要 ai_text 权限")
    return

providers = await ctx.ai.list_providers()
result = await ctx.ai.complete(
    system="你是一个简洁助手。",
    user="总结这段内容",
    provider_tag="chat",
    max_tokens=512,
    timeout_seconds=30,
)
await event.edit(result.text)
```

## Provider 选择

- `provider_tag`：推荐写法。按用途标签选择 provider，平台会在可用 provider 中挑选成本优先的匹配项。
- `provider`：需要固定 provider 时可传 provider id 或 provider name。
- `provider_hint`：兼容旧写法的别名；新模块优先使用 `provider` 或 `provider_tag`。
- `tag` / `tags`：兼容别名；新模块优先使用 `provider_tag`。

## Quota 与脱敏

- `ctx.ai.complete()` 复用平台 LLM Provider 池、fallback 链、账号级预算和 usage 记录。
- 插件传入的 `max_tokens` 与超时会被平台上限收紧，不能绕过账号配额。
- `ctx.ai.list_providers()` 只返回脱敏元数据，例如 provider 名称、默认模型、标签和成本层级。
- 插件不会拿到 `api_key_enc`、明文 API Key、`base_url` 或代理 URL。
- 不要在插件日志里记录用户完整隐私输入或模型完整输出；需要排障时只记录长度、截断摘要或 request id。

## 示例

完整最小示例见 `examples/plugins/with_ai/`。CI 只导入示例并校验 manifest / plugin 元数据，不会执行真实 AI 请求。
