"""
AutoGen Agent基类
所有AutoGen Agent都继承此类，提供标准化的接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from autogen_config import get_llm_config
import json


class BaseAutoGenAgent(ABC):
    """
    AutoGen Agent基类

    所有Agent都应该：
    1. 继承此类
    2. 实现system_message属性
    3. 可选地重写其他属性来自定义行为
    """

    def __init__(
        self,
        name: str,
        description: str,
        model: Optional[str] = None,
        temperature: float = 0.2,
        system_message: Optional[str] = None,
    ):
        """
        初始化 Agent

        Args:
            name: Agent名称
            description: Agent描述
            model: 使用的模型 (default: config中的default_model)
            temperature: 模型温度参数
            system_message: Agent的系统消息
        """
        self.name = name
        self.description = description
        self.model = model or "default"
        self.temperature = temperature
        self._system_message = system_message

    @property
    def system_message(self) -> str:
        """获取Agent的系统消息"""
        if self._system_message:
            return self._system_message
        # 默认系统消息
        return f"You are {self.name} - {self.description}"

    def get_config(self) -> Dict[str, Any]:
        """获取用于AutoGen的配置"""
        config = get_llm_config(self.model)
        config["temperature"] = self.temperature
        return config

    @abstractmethod
    def process(self, message: str, context: Dict[str, Any]) -> str:
        """
        处理消息并返回响应

        Args:
            message: 输入消息
            context: 上下文信息

        Returns:
            Agent的响应
        """
        pass

    def format_message(self, role: str, content: str) -> Dict[str, str]:
        """格式化消息"""
        return {
            "role": role,  # "user", "assistant", "system"
            "content": content,
        }

    def get_info(self) -> Dict[str, Any]:
        """获取Agent信息"""
        return {
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "temperature": self.temperature,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
