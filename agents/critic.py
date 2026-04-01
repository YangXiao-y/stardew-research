import json
from langchain_core.prompts import ChatPromptTemplate
from llm.client import get_llm
from llm.prompts import CRITIC_SYSTEM_PROMPT
from core.schemas import GapAnalysis, SubTask


class CriticAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.1)

    def run(self, question: str, subtasks: list[SubTask], evidence_pool: list[dict], next_task_id_start: int) -> GapAnalysis:
        prompt = ChatPromptTemplate.from_messages([
            ("system", CRITIC_SYSTEM_PROMPT),
            ("human", """
用户问题：{question}

当前子任务：
{subtasks}

当前证据池：
{evidence_pool}

请输出 JSON：
{{
  "enough": true,
  "missing_points": [],
  "new_subtasks": [
    {{
      "id": {next_task_id_start},
      "task": "...",
      "intent": "...",
      "status": "pending",
      "round_id": 2
    }}
  ]
}}
如果证据已经足够，则 new_subtasks 返回空数组。
""")
        ])

        chain = prompt | self.llm
        resp = chain.invoke({
            "question": question,
            "subtasks": subtasks,
            "evidence_pool": evidence_pool,
            "next_task_id_start": next_task_id_start,
        })
        text = resp.content.strip()

        try:
            data = json.loads(text)
            tasks = [SubTask(**x) for x in data.get("new_subtasks", [])]
            return GapAnalysis(
                enough=data.get("enough", True),
                missing_points=data.get("missing_points", []),
                new_subtasks=tasks,
            )
        except Exception:
            return GapAnalysis(enough=True, missing_points=[], new_subtasks=[])