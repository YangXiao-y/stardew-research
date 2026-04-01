"""
MCP版本的证据提取工具
将LLM证据提取标准化为MCP接口
"""

from typing import Dict, Any, List
from mcp_tools.base_mcp_tool import BaseMCPTool, ToolResult, ToolStatus
from tools.evidence_extractor import EvidenceExtractor
from core.schemas import SubTask, EvidenceItem


class EvidenceExtractorMCPTool(BaseMCPTool):
    """
    证据提取工具 (MCP版本)

    从网页内容中提取与任务相关的证据

    输入参数：
    {
        "subtask": {
            "id": int,
            "task": str,
            "intent": str,
            "status": str,
            "round_id": int
        },
        "title": str,              # 网页标题
        "url": str,                # 网页URL
        "page_text": str           # 网页内容
    }

    输出结果：
    {
        "status": "success" | "error",
        "data": {
            "evidences": [
                {
                    "subtask_id": int,
                    "content": str,
                    "source_type": str,
                    "source_url": str,
                    "source_title": str,
                    "confidence": float
                },
                ...
            ],
            "count": int
        }
    }
    """

    def __init__(self):
        super().__init__(
            name="evidence_extractor",
            description="Extract relevant evidence from webpage content for research subtasks.",
            version="1.0.0",
        )
        self.extractor = EvidenceExtractor()

    def validate_params(self, params: Dict[str, Any]) -> bool:
        """验证参数"""
        if not isinstance(params, dict):
            return False

        # 必需参数
        required = ["subtask", "title", "url", "page_text"]
        for param in required:
            if param not in params:
                return False

        # 验证subtask结构
        subtask = params["subtask"]
        if not isinstance(subtask, dict):
            return False

        required_subtask_fields = ["id", "task", "intent"]
        for field in required_subtask_fields:
            if field not in subtask:
                return False

        # 验证字符串参数
        if not isinstance(params["title"], str):
            return False
        if not isinstance(params["url"], str):
            return False
        if not isinstance(params["page_text"], str):
            return False

        return True

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        """执行证据提取"""
        try:
            # 重建SubTask对象
            subtask_dict = params["subtask"]
            subtask = SubTask(
                id=subtask_dict["id"],
                task=subtask_dict["task"],
                intent=subtask_dict["intent"],
                status=subtask_dict.get("status", "pending"),
                round_id=subtask_dict.get("round_id", 0),
            )

            # 调用原始提取函数
            evidence_items = self.extractor.run(
                subtask=subtask,
                title=params["title"],
                url=params["url"],
                page_text=params["page_text"],
            )

            # 转换为JSON兼容的格式
            formatted_evidence = []
            for item in evidence_items:
                formatted_evidence.append({
                    "subtask_id": item.subtask_id,
                    "content": item.content,
                    "source_type": item.source_type,
                    "source_url": item.source_url,
                    "source_title": item.source_title,
                    "confidence": item.confidence,
                })

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "evidences": formatted_evidence,
                    "count": len(formatted_evidence),
                },
                metadata={
                    "tool": "evidence_extractor",
                    "subtask_id": subtask.id,
                    "evidence_count": len(formatted_evidence),
                },
            )

        except Exception as e:
            return ToolResult(
                status=ToolStatus.ERROR,
                data=None,
                error_message=f"Evidence extraction failed: {str(e)}",
            )

    def get_schema(self) -> Dict[str, Any]:
        """获取工具Schema"""
        schema = super().get_schema()
        schema.update({
            "parameters": {
                "type": "object",
                "properties": {
                    "subtask": {
                        "type": "object",
                        "description": "The research subtask",
                        "properties": {
                            "id": {"type": "integer", "description": "Subtask ID"},
                            "task": {"type": "string", "description": "Task description"},
                            "intent": {"type": "string", "description": "Task intent/goal"},
                            "status": {"type": "string", "description": "Task status"},
                            "round_id": {"type": "integer", "description": "Research round ID"},
                        },
                        "required": ["id", "task", "intent"],
                    },
                    "title": {
                        "type": "string",
                        "description": "Webpage title",
                    },
                    "url": {
                        "type": "string",
                        "description": "Source URL",
                    },
                    "page_text": {
                        "type": "string",
                        "description": "Extracted text content from webpage",
                    },
                },
                "required": ["subtask", "title", "url", "page_text"],
            },
        })
        return schema
