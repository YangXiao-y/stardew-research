import json
from langchain_core.prompts import ChatPromptTemplate
from llm.client import get_llm
from llm.prompts import ROUTER_SYSTEM_PROMPT
from core.schemas import RouteResult


class RouterAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0)

    def run(self, question: str) -> RouteResult:
        prompt = ChatPromptTemplate.from_messages([
            ("system", ROUTER_SYSTEM_PROMPT),
            ("human", "用户问题：{question}\n请输出 JSON，如 {{\"question_type\": \"deep_research\"}}")
        ])

        chain = prompt | self.llm
        resp = chain.invoke({"question": question})
        text = resp.content.strip()

        try:
            data = json.loads(text)
            return RouteResult(**data)
        except Exception:
            if "research" in text.lower():
                return RouteResult(question_type="deep_research")
            if "strategy" in text.lower():
                return RouteResult(question_type="strategy_qa")
            return RouteResult(question_type="knowledge_qa")