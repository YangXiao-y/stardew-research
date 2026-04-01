"""
RouterAgent - 问题路由分类Agent
使用RoutingSkill来分类用户问题
"""

import json
from typing import Dict, Any
from autogen_agents.base_agent import BaseAutoGenAgent
from skills.routing_skill import RoutingSkill
from llm.client import get_llm


class RouterAgent(BaseAutoGenAgent):
    """
    路由Agent

    职责：
    - 分类用户问题为三种类型
    - deep_research: 需要深度研究的问题
    - strategy_qa: 游戏策略问题
    - knowledge_qa: 事实性知识问题
    """

    def __init__(self, model: str = "qwen"):
        super().__init__(
            name="Router",
            description="Classifier that determines question type and routing",
            model=model,
            temperature=0.0,  # 分类应该是确定性的
            system_message="You are a question classifier for Stardew Valley. Classify questions into categories.",
        )
        self.routing_skill = RoutingSkill()
        self.llm = get_llm(temperature=self.temperature)

    def process(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理消息并分类问题

        Args:
            message: 用户问题
            context: 上下文

        Returns:
            包含question_type的字典
        """
        try:
            # 使用Skill来处理
            skill_output = self.routing_skill.run(
                inputs={"question": message},
                llm_call_fn=self._llm_call,
            )

            return {
                "success": skill_output.success,
                "question_type": skill_output.question_type,
                "reasoning": skill_output.reasoning,
                "error": skill_output.error_message,
            }

        except Exception as e:
            return {
                "success": False,
                "question_type": "deep_research",  # 默认值
                "reasoning": "",
                "error": str(e),
            }

    def _llm_call(self, prompt: str) -> str:
        """调用LLM"""
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def format_output(self, process_result: Dict[str, Any]) -> str:
        """格式化输出为字符串"""
        return json.dumps(process_result, ensure_ascii=False, indent=2)
