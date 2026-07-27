"""Provider definitions for Verity API proxy.

Each provider represents an OpenAI-compatible LLM API endpoint.
"""

from dataclasses import dataclass


@dataclass
class Provider:
    """An LLM API provider with OpenAI-compatible chat completions endpoint."""

    name: str
    """Display name shown in the UI."""

    chat_url: str
    """Full chat completions URL, e.g. https://api.openai.com/v1/chat/completions"""

    default_model: str
    """Default model for this provider."""

    description: str = ""
    """Brief description shown in the UI."""


# Preset providers
PRESET_PROVIDERS: list[Provider] = [
    Provider(
        name="智谱 (Zhipu)",
        chat_url="https://open.bigmodel.cn/api/paas/v4/chat/completions",
        default_model="glm-4-flash",
        description="智谱 AI GLM 系列",
    ),
    Provider(
        name="DeepSeek",
        chat_url="https://api.deepseek.com/v1/chat/completions",
        default_model="deepseek-v4-flash",
        description="DeepSeek V4 系列",
    ),
    Provider(
        name="通义千问 (Tongyi)",
        chat_url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        default_model="qwen-turbo",
        description="阿里云通义千问",
    ),
    Provider(
        name="Moonshot (Kimi)",
        chat_url="https://api.moonshot.cn/v1/chat/completions",
        default_model="moonshot-v1-8k",
        description="月之暗面 Kimi",
    ),
    Provider(
        name="SiliconFlow",
        chat_url="https://api.siliconflow.cn/v1/chat/completions",
        default_model="Qwen/Qwen2.5-7B-Instruct",
        description="硅基流动 — 多种开源模型",
    ),
    Provider(
        name="OpenAI",
        chat_url="https://api.openai.com/v1/chat/completions",
        default_model="gpt-4o-mini",
        description="OpenAI 官方 API",
    ),
]



def find_provider(name: str) -> Provider | None:
    """Find a preset provider by name."""
    for p in PRESET_PROVIDERS:
        if p.name == name:
            return p
    return None
