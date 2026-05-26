# TelePilot 远程模块开发与安装指南

> 兼容入口已保留。正式正文请阅读 [TelePilot 远程模块](./PLUGIN-REMOTE.md) 和 [TelePilot 模块开发指南（索引）](./PLUGIN-DEV-GUIDE.md)。

远程模块和内置模块共用同一套 `Plugin` / `Manifest` / `PluginContext` 规范；区别只在远程模块额外需要 `plugin.json` 作为安装阶段静态元数据，并由 Git 仓库安装到 `plugins/installed/{name}/`。

建议直接阅读：

- [TelePilot 远程模块](./PLUGIN-REMOTE.md)
- [TelePilot 模块 API 参考](./PLUGIN-API-REFERENCE.md)
- [TelePilot 模块安全边界](./PLUGIN-SAFETY.md)
- [TelePilot 模块概览](./PLUGIN-OVERVIEW.md)

保留这个文件只是为了兼容旧链接；后续内容维护请更新新的拆分文档。
