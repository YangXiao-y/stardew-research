import json
from langchain_core.prompts import ChatPromptTemplate
from llm.client import get_llm
from llm.prompts import EVIDENCE_EXTRACTOR_SYSTEM_PROMPT
from core.schemas import EvidenceItem, SubTask
from tools.utils import detect_source_type


class EvidenceExtractor:
    def __init__(self):
        self.llm = get_llm(temperature=0.1)

    def run(self, subtask: SubTask, title: str, url: str, page_text: str) -> list[EvidenceItem]:
        prompt = ChatPromptTemplate.from_messages([
            ("system", EVIDENCE_EXTRACTOR_SYSTEM_PROMPT),
            ("human", """
子任务：{subtask_task}
页面标题：{title}
页面链接：{url}

页面正文：
{page_text}

请输出 JSON：
{{
  "evidences": [
    {{
      "snippet": "...",
      "evidence_role": "fact",
      "confidence": 0.8
    }}
  ]
}}

最多提取 2 条。
""")
        ])

        chain = prompt | self.llm
        resp = chain.invoke({
            "subtask_task": subtask.task,
            "title": title,
            "url": url,
            "page_text": page_text[:12000],
        })
        text = resp.content.strip()

        source_type = detect_source_type(url)

        try:
            data = json.loads(text)
            items = []
            for ev in data.get("evidences", []):
                items.append(EvidenceItem(
                    subtask_id=subtask.id,
                    source_type=source_type,
                    title=title,
                    url=url,
                    snippet=ev.get("snippet", ""),
                    evidence_role=ev.get("evidence_role", "fact"),
                    confidence=float(ev.get("confidence", 0.7))
                ))
            return items
        except Exception:
            fallback_snippet = page_text[:500].replace("\n", " ")
            return [EvidenceItem(
                subtask_id=subtask.id,
                source_type=source_type,
                title=title,
                url=url,
                snippet=fallback_snippet,
                evidence_role="fact",
                confidence=0.5
            )]