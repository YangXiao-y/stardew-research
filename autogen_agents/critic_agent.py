"""
CriticAgent - 批评评估Agent
使用AnalysisSkill评估收集的证据是否充分
"""

import json
from typing import Dict, Any, List
from autogen_agents.base_agent import BaseAutoGenAgent
from skills.analysis_skill import AnalysisSkill
from core.schemas import SubTask, EvidenceItem
from llm.client import get_llm


class CriticAgent(BaseAutoGenAgent):
    """
    批评Agent

    职责：
    - 评估收集的证据是否足以回答原始问题
    - 识别缺失的信息
    - 建议补充的研究方向
    """

    def __init__(self, model: str = "qwen"):
        super().__init__(
            name="Critic",
            description="Evaluates evidence sufficiency and identifies missing information",
            model=model,
            temperature=0.1,  # Even more deterministic than research
            system_message="You are a critical evaluator. Assess research quality and completeness.",
        )
        self.analysis_skill = AnalysisSkill()
        self.llm = get_llm(temperature=self.temperature)

    def process(
        self,
        question: str,
        subtasks: List[SubTask],
        evidence_pool: List[EvidenceItem],
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        评估证据

        Args:
            question: 原始问题
            subtasks: 所有子任务
            evidence_pool: 收集的证据池
            context: 上下文

        Returns:
            包含评估结果的字典
        """
        try:
            # 准备输入
            evidence_dicts = [
                {
                    "subtask_id": ev.subtask_id,
                    "content": ev.content[:200],  # 缩短以减少token用量
                    "source_type": ev.source_type,
                    "source_url": ev.source_url,
                    "source_title": ev.source_title,
                    "confidence": ev.confidence,
                }
                for ev in evidence_pool
            ]

            # 使用AnalysisSkill进行评估
            analysis_output = self.analysis_skill.run(
                inputs={
                    "question": question,
                    "subtasks": [{"id": t.id, "task": t.task, "intent": t.intent} for t in subtasks],
                    "evidence_pool": evidence_dicts,
                },
                llm_call_fn=self._llm_call,
            )

            # 转换new_subtasks为SubTask对象
            new_subtasks = []
            if analysis_output.new_subtasks:
                for task_dict in analysis_output.new_subtasks:
                    new_subtasks.append(
                        SubTask(
                            id=task_dict.get("id", 0),
                            task=task_dict.get("task", ""),
                            intent=task_dict.get("intent", ""),
                            status="pending",
                            round_id=0,
                        )
                    )

            return {
                "success": analysis_output.success,
                "enough": analysis_output.enough,
                "missing_points": analysis_output.missing_points,
                "new_subtasks": new_subtasks,
                "confidence_level": analysis_output.confidence_level,
                "error": analysis_output.error_message,
            }

        except Exception as e:
            return {
                "success": False,
                "enough": True,  # 默认认为足够，避免无限循环
                "missing_points": [],
                "new_subtasks": [],
                "confidence_level": 0.0,
                "error": str(e),
            }

    def _llm_call(self, prompt: str) -> str:
        """调用LLM"""
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def format_output(self, process_result: Dict[str, Any]) -> str:
        """格式化输出"""
        output = {
            "success": process_result["success"],
            "enough": process_result["enough"],
            "missing_points": process_result.get("missing_points", []),
            "new_subtasks_count": len(process_result.get("new_subtasks", [])),
            "confidence_level": process_result.get("confidence_level", 0),
        }
        return json.dumps(output, ensure_ascii=False, indent=2)
