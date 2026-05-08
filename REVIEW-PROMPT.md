# TeleBot 项目审查提示词

## 项目概览

TeleBot 是一个 Telegram UserBot 多账号管理平台，技术栈：
- 后端: Python 3.12 + FastAPI + SQLAlchemy 2 + Alembic + Redis
- 前端: React 18 + TypeScript + TailwindCSS + TanStack Query
- Telegram: Telethon 1.43+ (UserBot 模式)
- Worker: 每个账号独立子进程，Redis IPC 通信
- 插件系统: Plugin 基类 + loader + generation guard 热重载
- LLM: 多 provider 支持（openrouter / anyrouter / nvidia / yunai / qwen）
- 仓库: https://github.com/Anoyou/telebot

---

## 审查维度

### 一、LLM 集成（重点）

请审查以下方面：

1. **Provider 架构**：多 provider fallback 是否可靠、配置灵活度
2. **调用链路**：UserBot → Telethon → Plugin → LLM Provider → API，超时/重试/降级
3. **Telegram 场景特有问题**：
   - 消息长度限制（单条 4096 字符）
   - msg.edit 作为流式输出替代
   - LLM 回复 HTML 格式化（`<b>` `<code>` 等）
   - 长回复分段发送
4. **安全性**：Prompt 注入防护、API Key 加密存储、敏感信息泄露
5. **成本控制**：token 用量统计、调用频率限制、模型选择成本意识
6. **扩展建议**：流式输出、多轮对话上下文、结果缓存、A/B 测试

### 二、插件系统（重点）

1. **生命周期**：启动/热重载/卸载/异常隔离
2. **远程插件**：git clone 安全性、manifest 验证、热加载可靠性
3. **config_schema 两级配置**：全局/账号配置优先级、JSON Schema 验证
4. **owner_only 安全机制**：UserBot 模式防护、Sudo 豁免
5. **插件与 Worker 交互**：权限边界、命令派发、消息通道过滤
6. **优化建议**：依赖管理、版本兼容、配置表单、测试覆盖

### 三、架构 & 安全

Worker 隔离、Redis IPC 容错、Flood Wait 处理、Session 加密、JWT 安全、Alembic 迁移管理

---

## 输出格式

每个发现：
- **[P0/P1/P2] 标题**
- 描述 / 文件+行号 / 影响场景 / 修复方案

最后给出：修复优先级排序 + 短期路线图(1-2周) + 中期建议(1-3月) + 测试覆盖率分析
