"""
AnalysisSkill - 证据评估
评估收集的证据是否充分，识别缺失点
"""

import json
from typing import Dict, Any, List, Optional
from pydantic import Field, BaseModel
from skills.base_skill import BaseSkill, BaseSkillOutput


class SubTaskForAnalysis(BaseModel):
    """用于分析的子任务"""
    id: int
    task: str
    intent: str


class AnalysisSkillOutput(BaseSkillOutput):
    """AnalysisSkill输出"""
    enough: bool = Field(..., description="证据是否充分")
    missing_points: List[str] = Field(..., description="缺失的要点")
    new_subtasks: Optional[List[Dict[str, Any]]] = Field(None, description="建议的新子任务")
    confidence_level: Optional[float] = Field(None, description="回答的置信度 (0-1)")


class AnalysisSkill(BaseSkill):
    """
    证据评估Skill

    输入：
    {
        "question": str,
        "subtasks": [...],
        "evidence_pool": [...]
    }

    输出：
    {
        "success": bool,
        "enough": bool,
        "missing_points": [...],
        "new_subtasks": [...],
        "confidence_level": float
    }
    """

    def __init__(self):
        super().__init__(
            name="analysis",
            description="Evaluate if collected evidence is sufficient to answer the question",
            output_schema=AnalysisSkillOutput,
        )

    def generate_prompt(self, inputs: Dict[str, Any]) -> str:
        """生成评估prompt"""
        question = inputs.get("question", "")
        subtasks = inputs.get("subtasks", [])
        evidence_pool = inputs.get("evidence_pool", [])

        # 格式化子任务
        subtasks_str = "\n".join(
            [f"- Task {t.get('id', '?')}: {t.get('task', '')}" for t in subtasks[:5]]
        )

        # 格式化证据摘要
        evidence_summary = f"Total evidence items: {len(evidence_pool)}"
        if evidence_pool:
            evidence_types = {}
            for ev in evidence_pool[:20]:
                source = ev.get("source_type", "unknown")
                evidence_types[source] = evidence_types.get(source, 0) + 1
            evidence_summary += "\nEvidence sources: " + str(evidence_types)

        prompt = f"""You are an expert evaluator of Stardew Valley research quality.

Original Question: {question}

Research Subtasks Completed:
{subtasks_str}

Evidence Collection Summary:
{evidence_summary}

Evaluate if the collected evidence is sufficient to comprehensively answer the original question.

Respond in JSON format:
{{
    "enough": true/false,
    "missing_points": ["point 1", "point 2", ...],
    "confidence_level": 0.0 to 1.0,
    "new_subtasks": [
        {{"id": X, "task": "...", "intent": "..."}}
    ] or []
}}

If "enough" is true, set new_subtasks to an empty list.
If enough is false, suggest 1-2 new subtasks to fill the gaps."""

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

            # 提取并验证字段
            enough = result.get("enough", False)
            missing_points = result.get("missing_points", [])
            confidence = result.get("confidence_level", 0.5)

            # 确保confidence在0-1之间
            if not isinstance(confidence, (int, float)):
                confidence = 0.5
            confidence = max(0.0, min(1.0, confidence))

            new_subtasks = []
            if not enough and "new_subtasks" in result:
                new_subtasks = result.get("new_subtasks", [])
                if not isinstance(new_subtasks, list):
                    new_subtasks = []

            return {
                "success": True,
                "enough": bool(enough),
                "missing_points": missing_points if isinstance(missing_points, list) else [],
                "new_subtasks": new_subtasks,
                "confidence_level": confidence,
            }

        except (json.JSONDecodeError, IndexError, KeyError, TypeError) as e:
            # 降级处理
            return {
                "success": True,
                "enough": True,  # 默认认为足够
                "missing_points": [],
                "new_subtasks": [],
                "confidence_level": 0.5,
            }
