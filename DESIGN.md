# Design: Verity-api 全面重写

## Problem

原项目是一个 48 行的 Flask 脚本，作为 Minecraft Verity 恐怖模组与大模型 API 之间的桥梁。代码存在大量问题（裸 except、硬编码假数据、路由错误、无鉴权、无错误处理），且只支持单一 provider、只有命令行交互、无系统托盘。

用户要求：
1. 支持多种 LLM provider（智谱、DeepSeek、OpenAI 等）
2. PyQt6 GUI 替代 CLI 输入
3. 关闭窗口最小化到系统托盘
4. 帮助选项
5. 改善所有潜在问题
6. 系统托盘完全参照 Get It 项目

## Context

- **现有代码**: 单文件 `verity`，Flask + requests，无 requirements.txt，无项目结构
- **下游消费者**: Minecraft Verity 模组，通过 LiteLLM 客户端访问
- **API 协议**: OpenAI 兼容的 `/chat/completions`（但路由应为 `/v1/chat/completions`）
- **参考实现**: `C:\Users\37549\Desktop\Vibe Coding\useful\Get It\get_it_pyqt\源文件` — 完整的 PyQt6 + 系统托盘模式
- **图标**: `C:\Users\37549\Desktop\icon.ico`
- **约束**: 必须保持与 Verity 模组的兼容性（LiteLLM 客户端期望的 API 格式）

## Options Considered

### Option A: 最小改动 — 修 Flask + 加 GUI 配置面板

在原有 Flask 基础上修 bug，另起一个 PyQt6 进程做配置面板，通过配置文件通信。

- **How**: Flask 服务读 JSON 配置文件，PyQt6 GUI 写配置文件。两个独立进程。
- **Pros**: 改动最小，Flask 逻辑基本不动
- **Cons**: 两个进程间通信脆弱、配置热更新复杂、架构丑陋
- **Risk**: 配置文件竞争写入，两个进程生命周期管理复杂

### Option B: PyQt6 一体化 — 内置 HTTP 服务器

将 HTTP 服务器嵌入 PyQt6 应用（用 Flask 或 aiohttp 跑在后台线程），GUI 和服务器在同一个进程。

- **How**: QThread 运行 Flask/aiohttp，主线程跑 Qt 事件循环。提供者配置存储在应用状态中。
- **Pros**: 单进程、状态共享简单、生命周期统一管理、打包分发方便
- **Cons**: Flask 在 QThread 中运行需要小心线程安全，但 requests 调用本身是 I/O，问题不大
- **Risk**: 低。Flask 的 dev server 在 QThread 中已被广泛验证可行。

### Option C: 完全异步 — aiohttp + asyncio

用 aiohttp 替代 Flask，在 asyncio 事件循环中运行，与 Qt 事件循环集成。

- **How**: 用 `qasync` 桥接 asyncio 和 Qt 事件循环
- **Pros**: 非阻塞 I/O，性能更好，代码现代
- **Cons**: 引入额外依赖，增加复杂度，对这个小代理来说过度设计
- **Risk**: `qasync` 兼容性问题，调试困难

## Recommended: Option B

**理由**:
- 单进程架构最简单可靠
- 参考项目 Get It 已经验证了 PyQt6 + QThread 后台任务模式
- Flask 在 QThread 中运行是常见模式，稳定
- 打包成一个 exe 对 MC 玩家友好

## Implementation Outline

1. **项目结构**: 标准 Python 包结构（`server.py`, `providers.py`, `app.py`, `main.py`）
2. **Provider 系统**: 预置常见 provider（OpenAI, DeepSeek, 智谱, 通义千问等），支持自定义
3. **PyQt6 GUI**: 设置窗口 + 系统托盘，参考 Get It 的 `closeEvent` 和 `_create_tray_icon` 模式
4. **Flask 修复**: 正确的错误处理、真实的 token 计数（或至少合理估算）、正确的路由 `/v1/chat/completions`、streaming 支持
5. **配置持久化**: QSettings 或 JSON 文件保存 provider 配置
6. **帮助系统**: 关于对话框 + 简要使用说明

## Open Questions

- 是否需要 streaming 支持？（Verity 模组可能用 SSE）— 默认需要
- 是否需要多模型同时服务？（一个实例代理多个模型）— 暂不需要，保持简单
- 打包方式？PyInstaller？Nuitka？— 后期考虑，先保证代码能跑
