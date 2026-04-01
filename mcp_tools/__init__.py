"""
MCP工具注册表和初始化
"""

from mcp_tools.base_mcp_tool import (
    BaseMCPTool,
    MCPToolRegistry,
    ToolResult,
    ToolStatus,
    register_tool,
    get_tool_registry,
    call_tool,
)
from mcp_tools.search_mcp import SearchMCPTool
from mcp_tools.web_reader_mcp import WebReaderMCPTool
from mcp_tools.evidence_extractor_mcp import EvidenceExtractorMCPTool


def initialize_mcp_tools() -> MCPToolRegistry:
    """
    初始化所有MCP工具并注册

    Returns:
        MCPToolRegistry: 已填充的工具注册表
    """
    registry = get_tool_registry()

    # 注册所有工具
    search_tool = SearchMCPTool()
    web_reader_tool = WebReaderMCPTool()
    evidence_tool = EvidenceExtractorMCPTool()

    register_tool(search_tool)
    register_tool(web_reader_tool)
    register_tool(evidence_tool)

    return registry


__all__ = [
    "BaseMCPTool",
    "MCPToolRegistry",
    "ToolResult",
    "ToolStatus",
    "register_tool",
    "get_tool_registry",
    "call_tool",
    "SearchMCPTool",
    "WebReaderMCPTool",
    "EvidenceExtractorMCPTool",
    "initialize_mcp_tools",
]
