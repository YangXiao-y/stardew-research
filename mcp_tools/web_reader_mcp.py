"""
MCP版本的网页阅读器工具
将Browserless网页爬取标准化为MCP接口
"""

from typing import Dict, Any, Optional
from mcp_tools.base_mcp_tool import BaseMCPTool, ToolResult, ToolStatus
from tools.web_reader import fetch_page_text


class WebReaderMCPTool(BaseMCPTool):
    """
    网页阅读器工具 (MCP版本)

    从URL获取网页内容并转换为纯文本

    输入参数：
    {
        "url": str,                    # 网页URL
        "max_length": int (optional)   # 最大字符数，默认5000
    }

    输出结果：
    {
        "status": "success" | "error",
        "data": {
            "url": str,
            "content": str,           # 网页纯文本内容
            "length": int,
            "truncated": bool
        }
    }
    """

    def __init__(self):
        super().__init__(
            name="web_reader",
            description="Fetch and extract text content from a webpage URL.",
            version="1.0.0",
        )
        self.max_default_length = 5000

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数"""
        if not isinstance(params, dict):
            return False

        # 必需参数
        if "url" not in params:
            return False

        if not isinstance(params["url"], str) or len(params["url"]) == 0:
            return False

        # 验证URL格式 (简单检查)
        url = params["url"]
        if not (url.startswith("http://") or url.startswith("https://")):
            return False

        # 可选参数验证
        if "max_length" in params:
            if not isinstance(params["max_length"], int) or params["max_length"] <= 0:
                return False

        return True

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行网页读取"""
        try:
            url = params["url"]
            max_length = params.get("max_length", self.max_default_length)

            # 调用原始网页获取函数
            page_text = fetch_page_text(url)

            if page_text is None:
                page_text = ""

            # 检查是否需要截断
            truncated = len(page_text) > max_length
            if truncated:
                page_text = page_text[:max_length]

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "url": url,
                    "content": page_text,
                    "length": len(page_text),
                    "truncated": truncated,
                },
                metadata={
                    "tool": "web_reader",
                    "original_length": len(page_text),
                    "truncated": truncated,
                },
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                data=None,
                error_message=f"Web reading failed: {str(e)}",
            )

    def get_schema(self) -> Dict[str, Any]:
        """获取工具Schema"""
        schema = super().get_schema()
        schema.update({
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL of the webpage to fetch",
                    },
                    "max_length": {
                        "type": "integer",
                        "description": f"Maximum content length in characters (default: {self.max_default_length})",
                        "default": self.max_default_length,
                    },
                },
                "required": ["url"],
            },
        })
        return schema
