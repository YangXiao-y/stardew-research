"""
MCP工具基类 - Model Context Protocol Tool Interface
提供标准化的工具接口，支持AutoGen集成
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import json


class ToolStatus(Enum):
    """工具执行状态"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass
class ToolResult:
    """工具执行结果"""
    status: ToolStatus
    data: Any
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "data": self.data,
            "error_message": self.error_message,
            "metadata": self.metadata or {},
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class BaseMCPTool(ABC):
    """
    MCP工具基类

    所有工具都继承此类，提供标准化的接口：
    - 参数验证
    - 执行和错误处理
    - 结果标准化
    """

    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        """
        初始化工具

        Args:
            name: 工具名称 (e.g., "search", "web_reader", "evidence_extractor")
            description: 工具描述
            version: 工具版本
        """
        self.name = name
        self.description = description
        self.version = version

    @abstractmethod
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        验证输入参数

        Args:
            params: 输入参数字典

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """
        执行工具

        Args:
            params: 输入参数

        Returns:
            ToolResult: 执行结果
        """
        pass

    def __call__(self, params: Dict[str, Any]) -> ToolResult:
        """允许直接调用工具"""
        if not self.validate_params(params):
            return ToolResult(
                status=ToolStatus.ERROR,
                data=None,
                error_message=f"Invalid parameters for {self.name}",
            )

        try:
            return self.execute(params)
        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                data=None,
                error_message=str(e),
            )

    def get_schema(self) -> Dict[str, Any]:
        """
        获取工具的JSON Schema定义
        用于Agent了解工具的输入/输出格式
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "type": "function",
        }


class MCPToolRegistry:
    """
    MCP工具注册表
    管理所有注册的工具，支持查询和调用
    """

    def __init__(self):
        self._tools: Dict[str, BaseMCPTool] = {}

    def register(self, tool: BaseMCPTool) -> None:
        """注册工具"""
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """注销工具"""
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get_tool(self, tool_name: str) -> Optional[BaseMCPTool]:
        """获取工具"""
        return self._tools.get(tool_name)

    def call_tool(self, tool_name: str, params: Dict[str, Any]) -> ToolResult:
        """调用工具"""
        tool = self.get_tool(tool_name)
        if tool is None:
            return ToolResult(
                status=ToolStatus.ERROR,
                data=None,
                error_message=f"Tool '{tool_name}' not found",
            )
        return tool(params)

    def list_tools(self) -> List[str]:
        """列出所有已注册的工具"""
        return list(self._tools.keys())

    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """获取所有工具的Schema"""
        return [tool.get_schema() for tool in self._tools.values()]


# 全局工具注册表
_global_tool_registry = MCPToolRegistry()


def register_tool(tool: BaseMCPTool) -> None:
    """全局注册工具"""
    _global_tool_registry.register(tool)


def get_tool_registry() -> MCPToolRegistry:
    """获取全局工具注册表"""
    return _global_tool_registry


def call_tool(tool_name: str, params: Dict[str, Any]) -> ToolResult:
    """全局调用工具"""
    return _global_tool_registry.call_tool(tool_name, params)
