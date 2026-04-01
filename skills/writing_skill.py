"""
WritingSkill - 答案生成
基于证据生成最终答案
"""

import json
from typing import Dict, Any, List, Optional
from pydantic import Field
from skills.base_skill import BaseSkill, BaseSkillOutput


class WritingSkillOutput(BaseSkillOutput):
    """WritingSkill输出"""
    answer: str = Field(..., description="最终答案（Markdown格式）")
    structure: Optional[Dict[str, Any]] = Field(None, description="答案结构信息")
    sources_cited: Optional[int] = Field(None, description="引用的来源数")


class WritingSkill(BaseSkill):
    """
    答案生成Skill

    输入：
    {
        "question": str,
        "subtasks": [...],
        "evidence_pool": [...]
    }

    输出：
    {
        "success": bool,
        "answer": str (markdown),
        "structure": {...},
        "sources_cited": int
    }
    """

    def __init__(self):
        super().__init__(
            name="writing",
            description="Generate comprehensive final answer based on collected evidence",
            output_schema=WritingSkillOutput,
        )

    def generate_prompt(self, inputs: Dict[str, Any]) -> str:
        """生成答案生成prompt"""
        question = inputs.get("question", "")
        subtasks = inputs.get("subtasks", [])
        evidence_pool = inputs.get("evidence_pool", [])

        # 格式化证据摘要
        evidence_summary = f"Total evidence items available: {len(evidence_pool)}"

        prompt = f"""You are an expert writer synthesizing research into a comprehensive answer for a Stardew Valley question.

Original Question: {question}

Research Subtasks Completed:
{json.dumps([{{'id': t.get('id'), 'task': t.get('task')}} for t in subtasks[:5]], ensure_ascii=False)}

{evidence_summary}

Based on the research completed, write a comprehensive, well-structured answer to the original question.

Format the answer in Markdown with:
1. A clear conclusion/summary at the top
2. Detailed analysis with key points
3. Step-by-step recommendations (if applicable)
4. Important considerations/warnings

The answer should be practical and directly address the original question."""

        return prompt

    def parse_output(self, output: str) -> Dict[str, Any]:
        """解析LLM输出"""
        try:
            # 直接使用output作为答案
            answer = output.strip()

            # 简单的结构分析
            structure = {
                "has_headings": "#" in answer,
                "has_lists": ("- " in answer or "* " in answer),
                "paragraph_count": answer.count("\n\n"),
            }

            return {
                "success": True,
                "answer": answer,
                "structure": structure,
                "sources_cited": 0,  # 在这个阶段无法自动检测
            }

        except Exception as e:
            # 降级处理
            return {
                "success": True,
                "answer": output if output else "Unable to generate answer",
                "structure": {},
                "sources_cited": 0,
            }
