# Verity API Proxy

为 Minecraft Verity 恐怖模组（原版）提供 LLM API 代理。

> Verity 是一个 AI 驱动的 Minecraft 恐怖模组。原版已从 CurseForge 下架，社区维护版 [Verity-CE](https://github.com/Esylmu/Verity-CE) 内置了 API 配置，**无需本代理**。如果你在用社区版，直接配置即可；本程序仅服务于原版用户。

本程序作为桥梁，将原版模组的 LiteLLM 请求转发到国内大模型 API（智谱 / DeepSeek / 通义千问 等）。

## 我应该用哪个？

| 模组版本 | 需要本程序？ | 说明 |
|---|---|---|
| [Verity-CE](https://github.com/Esylmu/Verity-CE)（社区版） | 不需要 | 内置 API 配置，直连大模型 |
| Verity JE（原版） | **需要** | 通过 LiteLLM 走代理，本程序起中转作用 |

## 特性

- 多 Provider 支持 — 智谱、DeepSeek、通义千问、Moonshot、SiliconFlow、OpenAI
- PyQt6 桌面界面 — 无需命令行操作
- 系统托盘 — 关闭窗口自动最小化，服务持续运行
- Streaming 支持 — 兼容 SSE 流式响应
- 自动依赖安装 — 首次运行自动检测并安装缺失包

## 安装

```bash
git clone https://github.com/wszzxzzxnb/Verity-api.git
cd Verity-api
python main.py   # 首次运行自动检测并安装缺失依赖
```

## 使用

1. 选择 Provider（或选择「自定义」手动输入 API 地址）
2. 填入 API Key
3. 确认模型名称
4. 点击 **启动服务**
5. 在原版 Verity 模组的 LiteLLM URL 中填入 `http://127.0.0.1:5000`
6. 关闭窗口 - 最小化到系统托盘，服务继续运行

系统托盘右键可选择「打开主界面」或「退出」。

## 支持的 Provider

| Provider | 默认模型 | 说明 |
|---|---|---|
| 智谱 (Zhipu) | glm-4-flash | 智谱 AI GLM 系列 |
| DeepSeek | deepseek-v4-flash | DeepSeek V4 系列 |
| 通义千问 (Tongyi) | qwen-turbo | 阿里云通义千问 |
| Moonshot (Kimi) | moonshot-v1-8k | 月之暗面 Kimi |
| SiliconFlow | Qwen/Qwen2.5-7B-Instruct | 硅基流动 |
| OpenAI | gpt-4o-mini | OpenAI 官方 |
| 自定义 | 任意 | 手动输入 |

## 技术栈

- **Flask** — HTTP 服务器
- **Waitress** — 生产级 WSGI
- **PyQt6** — 桌面 GUI
- **Requests** — 上游 API 调用

## 注意事项

- 本程序仅在本地 (`127.0.0.1`) 运行，不会暴露到公网
- API Key 仅存储在内存中，不会写入磁盘
- 请确保 API Key 有效且有足够余额
- 如果使用 [Verity-CE](https://github.com/Esylmu/Verity-CE)，直接用其 `config/verity-common.toml` 配置即可，无需本程序
