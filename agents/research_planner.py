import json
from langchain_core.prompts import ChatPromptTemplate
from llm.client import get_llm
from llm.prompts import RESEARCH_PLANNER_SYSTEM_PROMPT
from core.schemas import SearchPlan, SubTask


class ResearchPlannerAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.2)

    def run(self, question: str, subtask: SubTask) -> SearchPlan:
        prompt = ChatPromptTemplate.from_messages([
            ("system", RESEARCH_PLANNER_SYSTEM_PROMPT),
            ("human", """
                原始问题：{question}
                子任务：{subtask_task}
                意图：{subtask_intent}

                请输出 JSON：
                {{
                "subtask_id": {subtask_id},
                "search_queries": ["..."],
                "preferred_sources": ["wiki", "guide"],
                "search_focus": ["fact", "strategy"]
                }}
                """)
        ])

        chain = prompt | self.llm
        resp = chain.invoke({
            "question": question,
            "subtask_task": subtask.task,
            "subtask_intent": subtask.intent,
            "subtask_id": subtask.id,
        })
        text = resp.content.strip()

        try:
            data = json.loads(text)
            return SearchPlan(**data)
        except Exception:
            return SearchPlan(
                subtask_id=subtask.id,
                search_queries=[
                    f"Stardew Valley {subtask.task}",
                    f"site:zh.stardewvalleywiki.com {subtask.task}"
                ],
                preferred_sources=["wiki", "guide"],
                search_focus=["fact", "strategy"]
            )