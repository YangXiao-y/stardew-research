"""
改进的 ResearcherAgent v2 - 支持增量同步
减少Token冗余的关键优化
"""

import json
from typing import Dict, Any, List, Optional
from autogen_agents.base_agent import BaseAutoGenAgent
from skills.research_skill import ResearchSkill
from mcp_tools import get_tool_registry, call_tool
from core.schemas import SubTask, EvidenceItem
from core.conversation_memory import TokenCounter
from llm.client import get_llm


class ResearcherAgentV2(BaseAutoGenAgent):
    """
    改进的研究 Agent (v2)

    改进点:
    1. 增量同步: 只发送新增证据，不重复发送已知的
    2. 摘要模式: 当证据过多时，自动使用摘要代替全量
    3. Token计数: 动态调整prompt大小以适应token限制
    """

    def __init__(self, model: str = "qwen", enable_incremental: bool = True):
        super().__init__(
            name="Researcher (v2)",
            description="Optimized researcher with incremental sync and token management",
            model=model,
            temperature=0.2,
            system_message="You are a research strategist. Plan searches and analyze evidence.",
        )
        self.research_skill = ResearchSkill()
        self.llm = get_llm(temperature=self.temperature)
        self.tool_registry = get_tool_registry()

        # v2 特定的属性
        self.enable_incremental = enable_incremental
        self.previously_seen_evidence: List[EvidenceItem] = []  # 已看过的证据
        self.evidence_cache: Dict[str, EvidenceItem] = {}  # 证据缓存 (by ID)

    def process(
        self,
        question: str,
        subtask: SubTask,
        all_evidence: List[EvidenceItem] = None,
        new_evidence_only: List[EvidenceItem] = None,
        max_prompt_tokens: int = 2000,
        context: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        执行研究 (增量同步版本)

        Args:
            question: 原始问题
            subtask: 当前子任务
            all_evidence: 所有已收集的证据 (用于计算增量)
            new_evidence_only: 仅新增的证据 (如果提供，则使用此代替计算增量)
            max_prompt_tokens: 最大prompt token数
            context: 上下文

        Returns:
            包含research结果的字典
        """
        try:
            # 1. 计算要发送的证据
            if self.enable_incremental:
                evidence_to_send = self._compute_incremental_evidence(
                    all_evidence or [],
                    new_evidence_only
                )
                evidence_summary = self._summarize_evidence_for_prompt(
                    evidence_to_send,
                    max_prompt_tokens
                )
            else:
                # 降级: 使用全量证据
                evidence_summary = self._summarize_evidence_for_prompt(
                    all_evidence or [],
                    max_prompt_tokens
                )

            # 2. 生成优化的prompt
            optimized_prompt = self._generate_optimized_prompt(
                question,
                subtask,
                evidence_summary,
                max_prompt_tokens
            )

            # 3. 调用LLM获取搜索策略
            research_output = self.research_skill.run(
                inputs={
                    "question": question,
                    "subtask": {
                        "id": subtask.id,
                        "task": subtask.task,
                        "intent": subtask.intent,
                    },
                    "previous_findings": evidence_summary.get("summary", "")
                },
                llm_call_fn=self._llm_call,
            )

            if not research_output.success:
                return {
                    "success": False,
                    "evidence": [],
                    "error": research_output.error_message,
                    "tokens_used": 0,
                }

            # 4. 执行搜索
            all_evidence_found = []
            tokens_used = TokenCounter.count_tokens(optimized_prompt)

            for query in research_output.search_queries[:2]:
                evidence = self._search_and_extract(query, subtask)
                all_evidence_found.extend(evidence)

                # 更新缓存
                for ev in evidence:
                    self.previously_seen_evidence.append(ev)

            return {
                "success": True,
                "evidence": all_evidence_found,
                "search_queries": research_output.search_queries,
                "research_direction": research_output.research_direction,
                "evidence_summary": evidence_summary,
                "tokens_used": tokens_used,
                "incremental_used": self.enable_incremental,
                "error": None,
            }

        except Exception as e:
            return {
                "success": False,
                "evidence": [],
                "search_queries": [],
                "tokens_used": 0,
                "error": str(e),
            }

    def _compute_incremental_evidence(
        self,
        all_evidence: List[EvidenceItem],
        new_evidence_only: Optional[List[EvidenceItem]] = None
    ) -> List[EvidenceItem]:
        """
        计算增量证据 (新增的部分)

        v2 的关键优化: 只返回新的证据，不重复已知的
        """
        if new_evidence_only is not None:
            # 明确提供了新证据列表
            return new_evidence_only

        # 否则计算差异
        existing_ids = {ev.source_url for ev in self.previously_seen_evidence}
        incremental = [
            ev for ev in all_evidence
            if ev.source_url not in existing_ids
        ]

        return incremental

    def _summarize_evidence_for_prompt(
        self,
        evidence: List[EvidenceItem],
        max_tokens: int = 1500
    ) -> Dict[str, Any]:
        """
        为prompt总结证据

        策略:
        1. 如果证据少 (<500 tokens): 返回全部
        2. 如果证据适中 (500-1500 tokens): 返回全部但截断内容
        3. 如果证据多 (>1500 tokens): 返回摘要
        """
        if not evidence:
            return {
                "type": "empty",
                "summary": "还没有收集任何证据",
                "tokens": 0,
                "evidence_count": 0
            }

        # 计算总token
        total_tokens = sum(
            TokenCounter.count_tokens(f"{ev.source_title}: {ev.content}")
            for ev in evidence
        )

        if total_tokens <= max_tokens:
            # 可以发送全部
            evidence_text = self._format_evidence_full(evidence)
            return {
                "type": "full",
                "summary": evidence_text,
                "tokens": TokenCounter.count_tokens(evidence_text),
                "evidence_count": len(evidence)
            }

        elif total_tokens <= max_tokens * 1.5:
            # 截断内容
            evidence_text = self._format_evidence_truncated(evidence, max_tokens)
            return {
                "type": "truncated",
                "summary": evidence_text,
                "tokens": TokenCounter.count_tokens(evidence_text),
                "evidence_count": len(evidence)
            }

        else:
            # 使用摘要
            summary_text = self._create_evidence_abstract(evidence, max_tokens // 4)
            return {
                "type": "abstract",
                "summary": summary_text,
                "tokens": TokenCounter.count_tokens(summary_text),
                "evidence_count": len(evidence)
            }

    def _format_evidence_full(self, evidence: List[EvidenceItem]) -> str:
        """
        完整格式化证据
        """
        lines = ["已有证据:"]
        for i, ev in enumerate(evidence[:20], 1):  # 最多20个
            lines.append(f"{i}. {ev.source_title}")
            lines.append(f"   来源: {ev.source_type}")
            lines.append(f"   内容: {ev.content[:200]}")
            lines.append("")
        return "\n".join(lines)

    def _format_evidence_truncated(
        self,
        evidence: List[EvidenceItem],
        max_tokens: int
    ) -> str:
        """
        截断格式化证据 (缩短内容长度)
        """
        lines = [f"已有证据 ({len(evidence)} 条):"]
        tokens_used = 0

        for ev in evidence:
            ev_text = f"• {ev.source_title}: {ev.content[:100]}"
            ev_tokens = TokenCounter.count_tokens(ev_text)

            if tokens_used + ev_tokens > max_tokens:
                lines.append(f"... 还有 {len(evidence) - len(lines)} 条未显示")
                break

            lines.append(ev_text)
            tokens_used += ev_tokens

        return "\n".join(lines)

    def _create_evidence_abstract(
        self,
        evidence: List[EvidenceItem],
        max_tokens: int
    ) -> str:
        """
        创建证据摘要（高度压缩）
        """
        if not evidence:
            return ""

        # 按来源分类
        by_source = {}
        for ev in evidence:
            if ev.source_type not in by_source:
                by_source[ev.source_type] = 0
            by_source[ev.source_type] += 1

        # 构建摘要
        lines = [f"[证据摘要] 已收集 {len(evidence)} 条证据:"]
        for source, count in by_source.items():
            lines.append(f"  • {source}: {count} 条")

        # 添加最高置信度的证据
        top_evidence = sorted(evidence, key=lambda e: e.confidence, reverse=True)[:3]
        if top_evidence:
            lines.append("\n高置信度证据摘要:")
            for ev in top_evidence:
                lines.append(f"  • {ev.source_title[:50]}")

        return "\n".join(lines)

    def _generate_optimized_prompt(
        self,
        question: str,
        subtask: SubTask,
        evidence_summary: Dict[str, Any],
        max_tokens: int
    ) -> str:
        """
        生成优化的prompt
        """
        # 基础prompt
        base_prompt = f"""基于以下信息，为这个研究子任务生成搜索策略:

原始问题: {question}

当前子任务:
- 任务: {subtask.task}
- 意图: {subtask.intent}

{evidence_summary['summary']}

请生成2-3个搜索查询来进一步研究这个子任务。"""

        # 计算prompt大小
        prompt_tokens = TokenCounter.count_tokens(base_prompt)

        if prompt_tokens > max_tokens:
            # 截断以适应token限制
            available_for_evidence = max_tokens - (prompt_tokens - len(evidence_summary['summary']))
            # 重新创建摘要
            evidence_summary = self._summarize_evidence_for_prompt(
                [],  # 空列表, 只返回基本摘要
                available_for_evidence
            )

        return base_prompt

    def _search_and_extract(
        self,
        query: str,
        subtask: SubTask
    ) -> List[EvidenceItem]:
        """
        搜索并提取证据 (与原版本相同)
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

    def get_optimization_stats(self) -> Dict[str, Any]:
        """
        获取优化统计信息
        """
        return {
            "incremental_enabled": self.enable_incremental,
            "previously_seen_evidence": len(self.previously_seen_evidence),
            "cache_size": len(self.evidence_cache),
        }
