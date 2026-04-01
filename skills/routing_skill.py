"""
RoutingSkill - 问题分类
将用户问题分类为三种类型：deep_research, strategy_qa, knowledge_qa
"""

import json
from typing import Dict, Any, Optional
from pydantic import Field
from skills.base_skill import BaseSkill, BaseSkillOutput


class RoutingSkillOutput(BaseSkillOutput):
    """RoutingSkill输出"""
    question_type: str = Field(..., description="问题类型: deep_research, strategy_qa, 或 knowledge_qa")
    reasoning: Optional[str] = Field(None, description="分类的推理")


class RoutingSkill(BaseSkill):
    """
    问题分类Skill

    输入：
    {
        "question": str
    }

    输出：
    {
        "success": bool,
        "question_type": "deep_research" | "strategy_qa" | "knowledge_qa",
        "reasoning": str
    }
    """

    def __init__(self):
        super().__init__(
            name="routing",
            description="Classify user questions into categories: deep_research, strategy_qa, knowledge_qa",
            output_schema=RoutingSkillOutput,
        )

    def generate_prompt(self, inputs: Dict[str, Any]) -> str:
        """生成分类prompt"""
        question = inputs.get("question", "")

        prompt = f"""You are an expert question classifier for Stardew Valley game questions.

Classify the following question into ONE of these categories:
1. "deep_research" - Complex questions requiring thorough research (e.g., optimized farming strategies, multi-year planning)
2. "strategy_qa" - Game strategy questions (e.g., best crops for spring, optimal barn placement)
3. "knowledge_qa" - Factual questions (e.g., what time does the shop close, where to find items)

Question: {question}

Respond in JSON format:
{{
    "question_type": "deep_research" | "strategy_qa" | "knowledge_qa",
    "reasoning": "brief explanation of why you chose this category"
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

            # 验证question_type
            valid_types = ["deep_research", "strategy_qa", "knowledge_qa"]
            if result.get("question_type") not in valid_types:
                result["question_type"] = "deep_research"  # 默认值

            return {
                "success": True,
                "question_type": result.get("question_type", "deep_research"),
                "reasoning": result.get("reasoning", ""),
            }

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            # 降级处理 - 尝试从文本中提取
            output_lower = output.lower()
            if "deep_research" in output_lower or "complex" in output_lower:
                q_type = "deep_research"
            elif "strategy" in output_lower:
                q_type = "strategy_qa"
            else:
                q_type = "knowledge_qa"

            return {
                "success": True,
                "question_type": q_type,
                "reasoning": "Fallback classification based on text analysis",
            }
