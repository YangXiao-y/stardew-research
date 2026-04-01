"""
MCP版本的搜索工具
将Serper搜索API标准化为MCP接口
"""

from typing import Dict, Any, List, Optional
from mcp_tools.base_mcp_tool import BaseMCPTool, ToolResult, ToolStatus
from tools.serper_search import serper_search, SearchResult
from dataclasses import dataclass


@dataclass
class SearchToolResult:
    """搜索结果"""
    query: str
    results: List[Dict[str, Any]]
    total_results: int


class SearchMCPTool(BaseMCPTool):
    """
    搜索工具 (MCP版本)

    输入参数：
    {
        "query": str,              # 搜索关键词
        "num": int (optional),     # 返回结果数，默认5
        "language": str (optional) # 搜索语言，默认"en"
    }

    输出结果：
    {
        "status": "success" | "error",
        "data": {
            "query": str,
            "results": [
                {
                    "title": str,
                    "link": str,
                    "snippet": str,
                    "position": int
                },
                ...
            ],
            "total_results": int
        }
    }
    """

    def __init__(self):
        super().__init__(
            name="search",
            description="Search the web using Google Serper API. Returns relevant results for Stardew Valley queries.",
            version="1.0.0",
        )

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数"""
        if not isinstance(params, dict):
            return False

        # 必需参数
        if "query" not in params:
            return False

        if not isinstance(params["query"], str) or len(params["query"]) == 0:
            return False

        # 可选参数验证
        if "num" in params and not isinstance(params["num"], int):
            return False

        if "language" in params and not isinstance(params["language"], str):
            return False

        return True

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行搜索"""
        try:
            query = params["query"]
            num = params.get("num", 5)

            # 调用原始搜索函数
            results: List[SearchResult] = serper_search(query, num=num)

            # 转换为字典格式
            formatted_results = []
            for i, result in enumerate(results):
                formatted_results.append({
                    "position": i + 1,
                    "title": result.title,
                    "link": result.link,
                    "snippet": result.snippet,
                })

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "query": query,
                    "results": formatted_results,
                    "total_results": len(formatted_results),
                },
                metadata={"tool": "search", "num_results": len(formatted_results)},
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                data=None,
                error_message=f"Search failed: {str(e)}",
            )

    def get_schema(self) -> Dict[str, Any]:
        """获取工具Schema"""
        schema = super().get_schema()
        schema.update({
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query keywords",
                    },
                    "num": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5, max: 10)",
                        "default": 5,
                    },
                    "language": {
                        "type": "string",
                        "description": "Search language (default: en)",
                        "default": "en",
                    },
                },
                "required": ["query"],
            },
        })
        return schema
