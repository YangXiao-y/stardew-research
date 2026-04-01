"""
ResearchSkill - 搜索策划
为每个子任务生成搜索查询和研究方向
"""

import json
from typing import Dict, Any, List, Optional
from pydantic import Field
from skills.base_skill import BaseSkill, BaseSkillOutput


class ResearchSkillOutput(BaseSkillOutput):
    """ResearchSkill输出"""
    search_queries: List[str] = Field(..., description="生成的搜索查询列表")
    research_direction: str = Field(..., description="研究方向说明")
    expected_sources: Optional[List[str]] = Field(None, description="预期的信息来源")


class ResearchSkill(BaseSkill):
    """
    搜索策划Skill

    输入：
    {
        "question": str,
        "subtask": {
            "id": int,
            "task": str,
            "intent": str
        },
        "existing_evidence": list  # optional
    }

    输出：
    {
        "success": bool,
        "search_queries": ["query1", "query2", ...],
        "research_direction": str,
        "expected_sources": [...]
    }
    """

    def __init__(self):
        super().__init__(
            name="research",
            description="Generate search queries and research strategy for a subtask",
            output_schema=ResearchSkillOutput,
        )

    def generate_prompt(self, inputs: Dict[str, Any]) -> str:
        """生成搜索策划prompt"""
        question = inputs.get("question", "")
        subtask = inputs.get("subtask", {})
        task = subtask.get("task", "")
        intent = subtask.get("intent", "")

        prompt = f"""You are an expert Stardew Valley researcher. Generate effective search queries for this research subtask.

Original Question: {question}

Subtask to Research:
- Task: {task}
- Intent: {intent}

Generate 2-3 specific, effective search queries that will help research this subtask.
Optimize queries for web search engines (Google, DuckDuckGo).

Respond in JSON format:
{{
    "search_queries": [
        "optimized search query 1",
        "optimized search query 2",
        "optimized search query 3"
    ],
    "research_direction": "Explanation of how to approach this research",
    "expected_sources": ["Stardew Valley wiki", "Reddit", "Guides/blogs"]
}}"""

        return prompt

    def parse_output(self, output: str) -> Dict[str, Any]:
        """解析LLM输出"""
        try:
            # 尝试解析JSON
            json_str = output.strip()

            # 如果输出包含Markdown代码块，提取JSON
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()

            result = json.loads(json_str)

            # 提取搜索查询
            search_queries = result.get("search_queries", [])
            if not isinstance(search_queries, list):
                search_queries = [str(search_queries)]

            # 过滤空查询
            search_queries = [q for q in search_queries if q and isinstance(q, str)]

            # 默认至少一个查询
            if not search_queries:
                search_queries = ["general research"]

            return {
                "success": True,
                "search_queries": search_queries[:3],  # 最多3个查询
                "research_direction": result.get("research_direction", ""),
                "expected_sources": result.get("expected_sources", []),
            }

        except (json.JSONDecodeError, IndexError, KeyError, TypeError) as e:
            # 降级处理
            return {
                "success": True,
                "search_queries": ["Stardew Valley general information"],
                "research_direction": "Fallback: General web search",
                "expected_sources": ["Web search results"],
            }
