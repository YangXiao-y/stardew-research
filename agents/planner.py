import json
from langchain_core.prompts import ChatPromptTemplate
from llm.client import get_llm
from llm.prompts import PLANNER_SYSTEM_PROMPT
from core.schemas import SubTask


class PlannerAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.2)

    def run(self, question: str) -> list[SubTask]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", PLANNER_SYSTEM_PROMPT),
            ("human", """
用户问题：{question}

请输出 JSON：
{{
  "subtasks": [
    {{
      "id": 1,
      "task": "...",
      "intent": "...",
      "status": "pending",
      "round_id": 1
    }}
  ]
}}
""")
        ])

        chain = prompt | self.llm
        resp = chain.invoke({"question": question})
        text = resp.content.strip()

        try:
            data = json.loads(text)
            return [SubTask(**x) for x in data["subtasks"]]
        except Exception:
            return [
                SubTask(id=1, task="识别第一年社区中心关键收集包及季节限制", intent="bundle_planning"),
                SubTask(id=2, task="分析春季前期赚钱路线和作物选择", intent="profit_strategy"),
                SubTask(id=3, task="分析夏季收益路线与社区中心兼容性", intent="season_tradeoff"),
                SubTask(id=4, task="评估温室、下矿、社交与种田之间的优先级冲突", intent="tradeoff_analysis"),
            ]