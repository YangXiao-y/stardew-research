"""
WriterAgent - 答案生成Agent
使用WritingSkill基于证据生成最终答案
"""

import json
from typing import Dict, Any, List
from autogen_agents.base_agent import BaseAutoGenAgent
from skills.writing_skill import WritingSkill
from core.schemas import SubTask, EvidenceItem
from llm.client import get_llm


class WriterAgent(BaseAutoGenAgent):
    """
    写作Agent

    职责：
    - 综合所有收集的证据
    - 生成高质量的最终答案
    - 确保答案结构清晰、信息完整
    """

    def __init__(self, model: str = "qwen"):
        super().__init__(
            name="Writer",
            description="Synthesizes evidence into comprehensive final answers",
            model=model,
            temperature=0.3,  # 少量创意来生成更好的表述
            system_message="You are an expert writer. Create clear, comprehensive answers.",
        )
        self.writing_skill = WritingSkill()
        self.llm = get_llm(temperature=self.temperature)

    def process(
        self,
        question: str,
        subtasks: List[SubTask],
        evidence_pool: List[EvidenceItem],
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        生成最终答案

        Args:
            question: 原始问题
            subtasks: 所有子任务
            evidence_pool: 收集的证据池
            context: 上下文

        Returns:
            包含最终答案的字典
        """
        try:
            # 准备输入
            evidence_summary = self._summarize_evidence(evidence_pool)

            # 使用WritingSkill生成答案
            writing_output = self.writing_skill.run(
                inputs={
                    "question": question,
                    "subtasks": [
                        {
                            "id": t.id,
                            "task": t.task,
                            "intent": t.intent,
                        }
                        for t in subtasks
                    ],
                    "evidence_pool": evidence_summary,
                },
                llm_call_fn=self._llm_call,
            )

            return {
                "success": writing_output.success,
                "answer": writing_output.answer,
                "structure": writing_output.structure,
                "sources_cited": writing_output.sources_cited,
                "evidence_count": len(evidence_pool),
                "error": writing_output.error_message,
            }

        except Exception as e:
            return {
                "success": False,
                "answer": "",
                "structure": {},
                "sources_cited": 0,
                "evidence_count": 0,
                "error": str(e),
            }

    def _summarize_evidence(self, evidence_pool: List[EvidenceItem]) -> List[Dict[str, Any]]:
        """
        总结证据池

        Args:
            evidence_pool: 证据列表

        Returns:
            简化的证据摘要
        """
        summary = []
        seen_content = set()

        for ev in evidence_pool[:30]:  # 最多30个证据以避免token过多
            # 避免重复
            content_key = (ev.source_type, ev.content[:100])
            if content_key in seen_content:
                continue

            seen_content.add(content_key)
            summary.append({
                "source_type": ev.source_type,
                "content": ev.content[:500],  # 限制长度
                "source_title": ev.source_title,
                "confidence": ev.confidence,
            })

        return summary

    def _llm_call(self, prompt: str) -> str:
        """调用LLM"""
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def format_output(self, process_result: Dict[str, Any]) -> str:
        """格式化输出"""
        output = {
            "success": process_result["success"],
            "answer_length": len(process_result.get("answer", "")),
            "evidence_used": process_result.get("evidence_count", 0),
            "sources_cited": process_result.get("sources_cited", 0),
        }
        return json.dumps(output, ensure_ascii=False, indent=2)
