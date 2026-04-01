"""
ResearcherAgent - 研究执行Agent
使用ResearchSkill生成搜索查询并执行研究
"""

import json
from typing import Dict, Any, List
from autogen_agents.base_agent import BaseAutoGenAgent
from skills.research_skill import ResearchSkill
from mcp_tools import get_tool_registry, call_tool
from core.schemas import SubTask, EvidenceItem
from llm.client import get_llm


class ResearcherAgent(BaseAutoGenAgent):
    """
    研究Agent

    职责：
    - 制定研究策略和搜索查询
    - 执行搜索并获取网页内容
    - 从网页中提取证据
    """

    def __init__(self, model: str = "qwen"):
        super().__init__(
            name="Researcher",
            description="Executes research by generating searches and extracting evidence",
            model=model,
            temperature=0.2,
            system_message="You are a research strategist. Plan searches and analyze evidence.",
        )
        self.research_skill = ResearchSkill()
        self.llm = get_llm(temperature=self.temperature)
        self.tool_registry = get_tool_registry()

    def process(
        self,
        question: str,
        subtask: SubTask,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        执行研究

        Args:
            question: 原始问题
            subtask: 当前子任务
            context: 上下文

        Returns:
            包含evidence的字典
        """
        try:
            # 第1步：使用ResearchSkill生成搜索查询
            research_output = self.research_skill.run(
                inputs={
                    "question": question,
                    "subtask": {
                        "id": subtask.id,
                        "task": subtask.task,
                        "intent": subtask.intent,
                    },
                },
                llm_call_fn=self._llm_call,
            )

            if not research_output.success:
                return {
                    "success": False,
                    "evidence": [],
                    "error": research_output.error_message,
                }

            # 第2步：执行搜索
            all_evidence = []
            for query in research_output.search_queries[:2]:
                evidence = self._search_and_extract(query, subtask)
                all_evidence.extend(evidence)

            return {
                "success": True,
                "evidence": all_evidence,
                "search_queries": research_output.search_queries,
                "research_direction": research_output.research_direction,
                "error": None,
            }

        except Exception as e:
            return {
                "success": False,
                "evidence": [],
                "search_queries": [],
                "error": str(e),
            }

    def _search_and_extract(self, query: str, subtask: SubTask) -> List[EvidenceItem]:
        """
        搜索并提取证据

        Args:
            query: 搜索查询
            subtask: 子任务

        Returns:
            证据列表
        """
        evidence_list = []

        try:
            # 使用MCP搜索工具
            search_result = call_tool("search", {"query": query, "num": 5})

            if search_result.status.value != "success":
                return evidence_list

            # 遍历搜索结果
            for result in search_result.data.get("results", [])[:3]:
                url = result.get("link", "")
                if not url:
                    continue

                # 获取页面内容
                web_result = call_tool("web_reader", {"url": url, "max_length": 5000})

                if web_result.status.value != "success":
                    continue

                page_text = web_result.data.get("content", "")

                # 提取证据
                evidence_result = call_tool(
                    "evidence_extractor",
                    {
                        "subtask": {
                            "id": subtask.id,
                            "task": subtask.task,
                            "intent": subtask.intent,
                        },
                        "title": result.get("title", ""),
                        "url": url,
                        "page_text": page_text,
                    },
                )

                if evidence_result.status.value == "success":
                    for ev_dict in evidence_result.data.get("evidences", []):
                        evidence_item = EvidenceItem(
                            subtask_id=ev_dict.get("subtask_id", 0),
                            content=ev_dict.get("content", ""),
                            source_type=ev_dict.get("source_type", "web"),
                            source_url=ev_dict.get("source_url", ""),
                            source_title=ev_dict.get("source_title", ""),
                            confidence=ev_dict.get("confidence", 0.5),
                        )
                        evidence_list.append(evidence_item)

        except Exception as e:
            print(f"Error in search_and_extract: {e}")

        return evidence_list

    def _llm_call(self, prompt: str) -> str:
        """调用LLM"""
        response = self.llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)

    def format_output(self, process_result: Dict[str, Any]) -> str:
        """格式化输出"""
        output = {
            "success": process_result["success"],
            "evidence_count": len(process_result.get("evidence", [])),
            "search_queries": process_result.get("search_queries", []),
            "research_direction": process_result.get("research_direction", ""),
        }
        return json.dumps(output, ensure_ascii=False, indent=2)
