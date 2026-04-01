"""
PlannerAgent - 任务拆解Agent
使用PlanningSkill将问题分解为子任务
"""

import json
from typing import Dict, Any, List
from autogen_agents.base_agent import BaseAutoGenAgent
from skills.planning_skill import PlanningSkill
from core.schemas import SubTask
from llm.client import get_llm


class PlannerAgent(BaseAutoGenAgent):
    """
    规划Agent

    职责：
    - 接收分类后的问题
    - 将其分解为3-5个子任务
    - 为每个子任务定义目标和意图
    """

    def __init__(self, model: str = "qwen"):
        super().__init__(
            name="Planner",
            description="Breaks down complex questions into actionable subtasks",
            model=model,
            temperature=0.2,
            system_message="You are a task planner. Break down questions into concrete subtasks.",
        )
        self.planning_skill = PlanningSkill()
        self.llm = get_llm(temperature=self.temperature)

    def process(
        self,
        message: str,
        question_type: str = "deep_research",
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        处理消息并生成子任务

        Args:
            message: 用户问题
            question_type: 问题类型
            context: 上下文

        Returns:
            包含subtasks的字典
        """
        try:
            # 使用Skill来处理
            skill_output = self.planning_skill.run(
                inputs={
                    "question": message,
                    "question_type": question_type,
                },
                llm_call_fn=self._llm_call,
            )

            # 转换为SubTask对象
            subtasks = []
            for task in skill_output.subtasks:
                subtasks.append(
                    SubTask(
                        id=task.id,
                        task=task.task,
                        intent=task.intent,
                        status="pending",
                        round_id=0,
                    )
                )

            return {
                "success": skill_output.success,
                "subtasks": subtasks,
                "total_tasks": skill_output.total_tasks,
                "planning_strategy": skill_output.planning_strategy,
                "error": skill_output.error_message,
            }

        except Exception as e:
            return {
                "success": False,
                "subtasks": [],
                "total_tasks": 0,
                "planning_strategy": "",
                "error": str(e),
            }

    def _llm_call(self, prompt: str) -> str:
        """调用LLM"""
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def format_output(self, process_result: Dict[str, Any]) -> str:
        """格式化输出为字符串"""
        output = {
            "success": process_result["success"],
            "total_tasks": process_result["total_tasks"],
            "subtasks": [
                {
                    "id": t.id,
                    "task": t.task,
                    "intent": t.intent,
                }
                for t in process_result["subtasks"]
            ],
            "planning_strategy": process_result["planning_strategy"],
        }
        return json.dumps(output, ensure_ascii=False, indent=2)
