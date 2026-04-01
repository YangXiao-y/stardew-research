"""
PlanningSkill - 任务拆解
将复杂问题分解为多个可执行的子任务
"""

import json
from typing import Dict, Any, List, Optional
from pydantic import Field, BaseModel
from skills.base_skill import BaseSkill, BaseSkillOutput


class SubTaskSchema(BaseModel):
    """子任务模型"""
    id: int
    task: str
    intent: str


class PlanningSkillOutput(BaseSkillOutput):
    """PlanningSkill输出"""
    subtasks: List[SubTaskSchema] = Field(..., description="拆解后的子任务列表")
    total_tasks: int = Field(..., description="子任务总数")
    planning_strategy: Optional[str] = Field(None, description="拆解策略说明")


class PlanningSkill(BaseSkill):
    """
    任务拆解Skill

    输入：
    {
        "question": str,
        "question_type": str  # optional
    }

    输出：
    {
        "success": bool,
        "subtasks": [
            {"id": 1, "task": "...", "intent": "..."},
            ...
        ],
        "total_tasks": int,
        "planning_strategy": str
    }
    """

    def __init__(self):
        super().__init__(
            name="planning",
            description="Break down complex questions into 3-5 actionable subtasks",
            output_schema=PlanningSkillOutput,
        )

    def generate_prompt(self, inputs: Dict[str, Any]) -> str:
        """生成拆解prompt"""
        question = inputs.get("question", "")
        question_type = inputs.get("question_type", "deep_research")

        if question_type == "knowledge_qa":
            task_count = "1-2"
        elif question_type == "strategy_qa":
            task_count = "2-3"
        else:
            task_count = "3-5"

        prompt = f"""You are an expert at breaking down complex Stardew Valley questions into research subtasks.

Original Question: {question}
Question Type: {question_type}

Break down this question into {task_count} specific subtasks that can be researched independently. Each subtask should:
1. Be specific and actionable
2. Have a clear research intent
3. Build toward answering the original question

Respond in JSON format:
{{
    "subtasks": [
        {{
            "id": 1,
            "task": "Specific research task description",
            "intent": "What aspect of the question this addresses"
        }},
        ...
    ],
    "planning_strategy": "Brief explanation of how these subtasks address the original question"
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

            # 提取并验证subtasks
            subtasks_raw = result.get("subtasks", [])
            subtasks = []

            for i, task_dict in enumerate(subtasks_raw):
                subtasks.append({
                    "id": task_dict.get("id", i + 1),
                    "task": task_dict.get("task", "Task"),
                    "intent": task_dict.get("intent", "Research intent"),
                })

            return {
                "success": True,
                "subtasks": subtasks,
                "total_tasks": len(subtasks),
                "planning_strategy": result.get("planning_strategy", ""),
            }

        except (json.JSONDecodeError, IndexError, KeyError, TypeError) as e:
            # 降级处理 - 创建默认子任务
            return {
                "success": True,
                "subtasks": [
                    {
                        "id": 1,
                        "task": "Gather background information",
                        "intent": "Understand the topic context",
                    },
                    {
                        "id": 2,
                        "task": "Research specific strategies",
                        "intent": "Find practical recommendations",
                    },
                ],
                "total_tasks": 2,
                "planning_strategy": "Fallback planning strategy",
            }
