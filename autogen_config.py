"""
AutoGen框架配置管理
支持多个LLM模型：QWen, GPT-4, Claude
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ModelConfig:
    """LLM模型配置"""
    model_name: str
    api_key: str
    base_url: str
    temperature: float = 0.2
    max_tokens: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为AutoGen兼容的配置字典"""
        return {
            "model": self.model_name,
            "api_key": self.api_key,
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }


@dataclass
class AutoGenConfig:
    """AutoGen全局配置"""
    # 模型
    default_model: str = "qwen"
    available_models: Dict[str, ModelConfig] = field(default_factory=dict)

    # GroupChat配置
    max_conversation_rounds: int = 25
    enable_human_input: bool = False

    # Debug模式
    debug_mode: bool = False
    log_file: str = "autogen_debug.log"

    def get_model_config(self, model_name: str) -> ModelConfig:
        """获取指定模型配置"""
        if model_name not in self.available_models:
            raise ValueError(f"Unknown model: {model_name}. Available: {list(self.available_models.keys())}")
        return self.available_models[model_name]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "default_model": self.default_model,
            "available_models": {k: v.to_dict() for k, v in self.available_models.items()},
            "max_conversation_rounds": self.max_conversation_rounds,
            "enable_human_input": self.enable_human_input,
            "debug_mode": self.debug_mode,
        }


def create_default_config() -> AutoGenConfig:
    """创建默认配置，支持环境变量"""
    config = AutoGenConfig()

    # QWen 配置
    qwen_key = os.getenv("QWEN_API_KEY", "")
    qwen_url = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    config.available_models["qwen"] = ModelConfig(
        model_name=os.getenv("QWEN_MODEL", "qwen-plus"),
        api_key=qwen_key,
        base_url=qwen_url,
        temperature=0.2,
    )

    # GPT-4 配置 (如果有API Key)
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key:
        config.available_models["gpt4"] = ModelConfig(
            model_name="gpt-4",
            api_key=openai_key,
            base_url="https://api.openai.com/v1",
            temperature=0.2,
        )

    # Claude 配置 (如果有API Key)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        config.available_models["claude"] = ModelConfig(
            model_name="claude-3-opus-20240229",
            api_key=anthropic_key,
            base_url="https://api.anthropic.com/v1",
            temperature=0.2,
        )

    # 其他配置
    config.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
    config.enable_human_input = os.getenv("ENABLE_HUMAN_INPUT", "false").lower() == "true"

    return config


# 全局配置实例
autogen_config = create_default_config()


def get_llm_config(model_name: Optional[str] = None) -> Dict[str, Any]:
    """
    获取LLM配置，用于初始化AutoGen Agent

    Args:
        model_name: 模型名称，默认使用default_model

    Returns:
        AutoGen兼容的配置字典
    """
    if model_name is None:
        model_name = autogen_config.default_model

    model_config = autogen_config.get_model_config(model_name)
    return model_config.to_dict()


def get_all_available_models() -> list[str]:
    """获取所有可用的模型列表"""
    return list(autogen_config.available_models.keys())


def print_config_info():
    """打印配置信息（用于调试）"""
    print("=" * 60)
    print("AutoGen Configuration")
    print("=" * 60)
    print(f"Default Model: {autogen_config.default_model}")
    print(f"Available Models: {list(autogen_config.available_models.keys())}")
    print(f"Debug Mode: {autogen_config.debug_mode}")
    print(f"Human Input Enabled: {autogen_config.enable_human_input}")
    print("=" * 60)
