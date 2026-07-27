# Verity API Proxy

为 Minecraft [Verity](https://www.curseforge.com/minecraft/modpacks/veritypack) 恐怖模组提供 LLM API 代理。

Verity 是一个 Minecraft 恐怖模组，核心特色是 AI 驱动的神秘实体。本程序作为桥梁，将模组的 LiteLLM 请求转发到您配置的大模型 API（OpenAI / DeepSeek / 智谱 / 通义千问 等）。

## 特性

- 多 Provider 支持 — 预置 OpenAI、DeepSeek、智谱、通义千问、Moonshot、SiliconFlow
- PyQt6 桌面界面 — 无需命令行
- 系统托盘 — 关闭窗口自动最小化，服务持续运行
- Streaming 支持 — 兼容 SSE 流式响应
- 自动依赖安装 — 首次运行自动检查并安装缺失包

## 安装

```bash
# 克隆仓库
git clone https://github.com/wszzxzzxnb/Verity-api.git
cd Verity-api

# 安装依赖（或直接运行 main.py 自动安装）
pip install -r requirements.txt
```

## 使用

```bash
python main.py
```

1. 选择 Provider（或选择「自定义」手动输入 API 地址）
2. 填入 API Key
3. 确认模型名称
4. 点击 **启动服务**
5. 在 Verity 模组的 LiteLLM URL 中填入：`http://127.0.0.1:5000/v1/chat/completions`
6. 关闭窗口 → 最小化到系统托盘，服务继续运行

在系统托盘右键可选择「打开主界面」或「退出」。

## 支持的 Provider

| Provider | 默认模型 | API 地址 |
|---|---|---|
| OpenAI | gpt-4o-mini | api.openai.com |
| DeepSeek | deepseek-chat | api.deepseek.com |
| 智谱 (Zhipu) | glm-4-flash | open.bigmodel.cn |
| 通义千问 (Tongyi) | qwen-turbo | dashscope.aliyuncs.com |
| Moonshot (Kimi) | moonshot-v1-8k | api.moonshot.cn |
| SiliconFlow | Qwen/Qwen2.5-7B-Instruct | api.siliconflow.cn |
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
