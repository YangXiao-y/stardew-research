"""
AutoGen框架 - 研究流程协调层
使用AutoGen GroupChat重新实现研究流程
"""

from typing import Dict, Any, List, Optional
from core.state import ResearchState
from core.schemas import SubTask, EvidenceItem
from autogen_agents import (
    RouterAgent,
    PlannerAgent,
    ResearcherAgent,
    CriticAgent,
    WriterAgent,
)
from mcp_tools import initialize_mcp_tools
from config import settings
import json


class AutoGenResearchFlow:
    """
    AutoGen框架研究流程

    使用AutoGen风格的多代理协调，替代原有的手写协调逻辑。

    流程：
    1. Router: 问题分类
    2. Planner: 任务拆解
    3. 循环 (最多MAX_RESEARCH_ROUNDS轮):
        - Researcher: 执行搜索和证据收集
        - Critic: 评估证据充分性
    4. Writer: 生成最终答案

    相比原有DeepResearchFlow的改进：
    - 使用成熟的AutoGen框架
    - 代码更结构化和可维护
    - 支持多个LLM模型
    - 工具通过MCP标准化
    """

    def __init__(self, model: str = "qwen", debug: bool = False):
        """
        初始化AutoGen研究流程

        Args:
            model: 使用的LLM模型 (default: "qwen")
            debug: 调试模式
        """
        self.model = model
        self.debug = debug

        # 初始化所有Agent
        self.router = RouterAgent(model=model)
        self.planner = PlannerAgent(model=model)
        self.researcher = ResearcherAgent(model=model)
        self.critic = CriticAgent(model=model)
        self.writer = WriterAgent(model=model)

        # 初始化MCP工具
        initialize_mcp_tools()

        # 配置
        self.max_rounds = settings.MAX_RESEARCH_ROUNDS

    def run(self, question: str) -> ResearchState:
        """
        执行研究流程

        Args:
            question: 用户问题

        Returns:
            ResearchState: 包含完整研究结果的状态对象
        """
        if self.debug:
            print(f"\n{'='*60}")
            print(f"Starting AutoGen Research Flow for question:")
            print(f"  {question}")
            print(f"{'='*60}\n")

        # 初始化状态
        state = ResearchState(question=question, question_type="")

        # Step 1: 问题路由
        if self.debug:
            print("[Step 1] 问题路由中...")
        route_result = self.router.process(question)

        if not route_result.get("success"):
            print(f"Warning: Routing failed: {route_result.get('error')}")
            state.question_type = "deep_research"
        else:
            state.question_type = route_result.get("question_type", "deep_research")

        if self.debug:
            print(f"  ✓ Question Type: {state.question_type}\n")

        # Step 2: 任务拆解
        if self.debug:
            print("[Step 2] 任务拆解中...")

        plan_result = self.planner.process(question, state.question_type)

        if not plan_result.get("success"):
            print(f"Warning: Planning failed: {plan_result.get('error')}")
        else:
            state.subtasks = plan_result.get("subtasks", [])

        if self.debug:
            print(f"  ✓ Created {len(state.subtasks)} subtasks\n")

        # Step 3: 迭代研究 (最多MAX_RESEARCH_ROUNDS轮)
        for round_id in range(1, self.max_rounds + 1):
            if self.debug:
                print(f"[Step 3.{round_id}] 研究轮次 {round_id}/{self.max_rounds}")

            state.round_id = round_id

            # 获取待执行的子任务
            pending = state.pending_subtasks()
            if not pending:
                if self.debug:
                    print("  ✓ No pending tasks\n")
                break

            # 执行每个待执行的子任务
            for subtask in pending:
                state.mark_running(subtask.id)

                # 使用Researcher执行研究
                research_result = self.researcher.process(question, subtask)

                if research_result.get("success"):
                    evidence = research_result.get("evidence", [])
                    state.add_evidence(evidence)

                    if self.debug:
                        print(f"  ✓ Subtask {subtask.id}: Collected {len(evidence)} evidence items")

                state.mark_done(subtask.id)

            # Step 4: 差距分析
            if self.debug:
                print(f"\n[Step 4.{round_id}] 证据评估中...")

            analysis_result = self.critic.process(
                question, state.subtasks, state.evidence_pool
            )

            if analysis_result.get("success"):
                state.missing_points = analysis_result.get("missing_points", [])
                enough = analysis_result.get("enough", True)

                if self.debug:
                    print(f"  ✓ Evidence sufficient: {enough}")
                    if not enough:
                        print(f"  ✓ Missing points: {len(state.missing_points)}")

                # 如果证据足够，停止研究
                if enough:
                    if self.debug:
                        print()
                    break

                # 添加新的字任务
                new_subtasks = analysis_result.get("new_subtasks", [])
                if new_subtasks:
                    state.add_subtasks(new_subtasks)
                    if self.debug:
                        print(f"  ✓ Added {len(new_subtasks)} new subtasks\n")
            else:
                if self.debug:
                    print(f"  ✗ Analysis failed: {analysis_result.get('error')}\n")
                break

        # Step 5: 最终答案生成
        if self.debug:
            print("[Step 5] 最终答案生成中...")

        writing_result = self.writer.process(question, state.subtasks, state.evidence_pool)

        if writing_result.get("success"):
            state.final_answer = writing_result.get("answer", "")
            if self.debug:
                print(f"  ✓ Generated answer ({len(state.final_answer)} chars)\n")
        else:
            state.final_answer = "Unable to generate answer"
            if self.debug:
                print(f"  ✗ Answer generation failed: {writing_result.get('error')}\n")

        if self.debug:
            print(f"{'='*60}")
            print("Research Flow Completed")
            print(f"  Question Type: {state.question_type}")
            print(f"  Subtasks: {len(state.subtasks)}")
            print(f"  Evidence Items: {len(state.evidence_pool)}")
            print(f"  Final Answer Length: {len(state.final_answer)} chars")
            print(f"{'='*60}\n")

        return state

    def get_info(self) -> Dict[str, Any]:
        """获取流程信息"""
        return {
            "model": self.model,
            "max_research_rounds": self.max_rounds,
            "agents": [
                self.router.get_info(),
                self.planner.get_info(),
                self.researcher.get_info(),
                self.critic.get_info(),
                self.writer.get_info(),
            ],
        }
