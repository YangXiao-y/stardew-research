import json
from langchain_core.prompts import ChatPromptTemplate
from llm.client import get_llm
from llm.prompts import WRITER_SYSTEM_PROMPT


class WriterAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.3)

    @staticmethod
    def _safe_json_dumps(obj) -> str:
        return json.dumps(obj, ensure_ascii=False, indent=2)

    def run(self, question: str, subtasks: list, evidence_pool: list) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", WRITER_SYSTEM_PROMPT),
            ("human", """
用户问题：
{question}

研究子任务（JSON）：
{subtasks_json}

证据池（JSON）：
{evidence_pool_json}

请严格基于证据池输出，不要编造未在证据中出现的事实。
请按以下固定结构输出：

1. 结论
2. 分析
3. 阶段建议
4. 注意事项
""")
        ])

        subtasks_json = self._safe_json_dumps(subtasks)
        evidence_pool_json = self._safe_json_dumps(evidence_pool)

        chain = prompt | self.llm
        resp = chain.invoke({
            "question": question,
            "subtasks_json": subtasks_json,
            "evidence_pool_json": evidence_pool_json,
        })
        return resp.content.strip()