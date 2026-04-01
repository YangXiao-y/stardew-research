"""
多轮对话 AutoGen 研究流程 (v3)
支持记忆、增量同步、Token优化
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from core.state import ResearchState
from core.schemas import SubTask, EvidenceItem
from core.conversation_memory import (
    ConversationMemory,
    MessageRole,
    TokenCounter,
    Message
)
from autogen_agents import (
    RouterAgent,
    PlannerAgent,
    CriticAgent,
    WriterAgent,
)
from autogen_agents.researcher_agent_v2 import ResearcherAgentV2
from config import settings
import json


class MultiTurnAutoGenResearchFlow:
    """
    多轮对话 AutoGen 研究流程 (v3)

    特性:
    1. 多轮对话支持 - 用户可以继续提问
    2. 对话记忆 - 保存跨轮次的上下文
    3. 增量同步 - v2 ResearcherAgent 减少Token冗余
    4. Token管理 - 自动压缩和摘要
    """

    def __init__(
        self,
        model: str = "qwen",
        session_id: Optional[str] = None,
        debug: bool = False,
        enable_incremental_sync: bool = True
    ):
        """
        初始化多轮对话流程

        Args:
            model: LLM模型
            session_id: 会话ID (如果None则自动生成)
            debug: 调试模式
            enable_incremental_sync: 启用增量同步 (v2优化)
        """
        self.model = model
        self.session_id = session_id or f"session_{datetime.now().timestamp()}"
        self.debug = debug
        self.enable_incremental_sync = enable_incremental_sync

        # 初始化记忆系统
        self.memory = ConversationMemory(
            session_id=self.session_id,
            max_memory_tokens=8000,
            summary_interval=3
        )

        # 初始化 Agents (使用v2 ResearcherAgent)
        self.router = RouterAgent(model=model)
        self.planner = PlannerAgent(model=model)
        self.researcher = ResearcherAgentV2(
            model=model,
            enable_incremental=enable_incremental_sync
        )
        self.critic = CriticAgent(model=model)
        self.writer = WriterAgent(model=model)

        # 会话状态
        self.conversation_turns = []
        self.research_contexts = {}  # 每轮对话的研究上下文

        # 配置
        self.max_rounds = settings.MAX_RESEARCH_ROUNDS

    def run_turn(self, user_question: str) -> Dict[str, Any]:
        """
        运行单轮对话

        Args:
            user_question: 用户提问

        Returns:
            包含答案和元数据的字典
        """
        if self.debug:
            print(f"\n{'='*70}")
            print(f"多轮对话 - 轮次 {len(self.conversation_turns) + 1}")
            print(f"用户: {user_question}")
            print(f"{'='*70}\n")

        # 1. 获取历史上下文
        context = self.memory.get_context_window(user_question)
        if self.debug:
            print(f"[记忆] 压缩使用: {context['compression_used']}, "
                  f"Token: {context['tokens_used']}")

        # 2. 增强的问题
        enhanced_question = self._enhance_question_with_context(
            user_question,
            context
        )

        # 3. 执行研究流程
        result = self._execute_research_flow(enhanced_question)

        # 4. 记录到内存
        self.memory.add_message(
            role=MessageRole.USER,
            content=user_question,
            metadata={
                "turn": len(self.conversation_turns) + 1,
                "timestamp": datetime.now().isoformat()
            }
        )

        self.memory.add_message(
            role=MessageRole.ASSISTANT,
            content=result.get("answer", "")[:500],  # 摘要
            metadata={
                "turn": len(self.conversation_turns) + 1,
                "evidence_count": len(result.get("evidence_pool", [])),
                "question_type": result.get("question_type", "")
            }
        )

        self.memory.new_turn()

        # 5. 保存到会话记录
        turn_record = {
            "turn_number": len(self.conversation_turns) + 1,
            "user_question": user_question,
            "enhanced_question": enhanced_question,
            "result": result,
            "memory_stats": self.memory.get_memory_stats(),
            "timestamp": datetime.now().isoformat()
        }
        self.conversation_turns.append(turn_record)

        return {
            "success": result.get("success", False),
            "answer": result.get("final_answer", ""),
            "question_type": result.get("question_type", ""),
            "evidence_count": len(result.get("evidence_pool", [])),
            "used_history": context['compression_used'],
            "turn_number": len(self.conversation_turns),
            "memory_usage": f"{self.memory.get_memory_stats()['memory_utilization']}"
        }

    def run_multi_turn_session(self, questions: List[str]) -> Dict[str, Any]:
        """
        运行多轮对话会话

        Args:
            questions: 问题列表

        Returns:
            包含所有轮次结果的字典
        """
        results = []

        for i, question in enumerate(questions, 1):
            print(f"\n>>> 轮次 {i}/{len(questions)}")
            print(f"Q: {question}")

            turn_result = self.run_turn(question)

            print(f"A: {turn_result['answer'][:100]}...")

            if turn_result['used_history']:
                print("✓ 使用了历史记忆")
            print(f"  内存使用: {turn_result['memory_usage']}")

            results.append(turn_result)

        return {
            "session_id": self.session_id,
            "total_turns": len(questions),
            "results": results,
            "memory_summary": self.memory.export_session()['stats'],
            "optimization_stats": self._get_optimization_stats()
        }

    def _enhance_question_with_context(
        self,
        question: str,
        context: Dict[str, Any]
    ) -> str:
        """
        用历史上下文增强问题
        """
        if not context.get('messages'):
            return question

        # 构建上下文摘要
        context_lines = []

        if context.get('summary'):
            context_lines.append(f"之前讨论的: {context['summary'][:100]}")

        # 添加最近消息的摘要
        recent_msgs = context.get('messages', [])[-3:]
        if recent_msgs:
            context_lines.append("最近的讨论:")
            for msg in recent_msgs:
                if msg.role == MessageRole.USER:
                    context_lines.append(f"  用户: {msg.content[:50]}")

        if not context_lines:
            return question

        enhanced = (
            f"基于之前的讨论:\n"
            + "\n".join(context_lines) +
            f"\n\n现在的问题: {question}"
        )

        return enhanced if len(enhanced) < 2000 else question

    def _execute_research_flow(self, question: str) -> Dict[str, Any]:
        """
        执行单次研究流程 (内部方法)
        """
        state = ResearchState(question=question)

        # Step 1: 路由
        if self.debug:
            print("[Step 1] 问题路由...")
        route_result = self.router.process(question)
        state.question_type = route_result.get("question_type", "deep_research")

        if self.debug:
            print(f"  ✓ 类型: {state.question_type}")

        # Step 2: 规划
        if self.debug:
            print("[Step 2] 任务拆解...")
        plan_result = self.planner.process(question, state.question_type)
        state.subtasks = plan_result.get("subtasks", [])

        if self.debug:
            print(f"  ✓ 子任务数: {len(state.subtasks)}")

        # Step 3: 迭代研究 (使用v2优化)
        for round_id in range(1, self.max_rounds + 1):
            if self.debug:
                print(f"[Step 3.{round_id}] 研究轮次 {round_id}/{self.max_rounds}")

            state.round_id = round_id

            pending = state.pending_subtasks()
            if not pending:
                break

            # 执行研究 (使用增量同步)
            for subtask in pending:
                state.mark_running(subtask.id)

                # v2优化: 计算增量证据
                new_evidence = None
                if self.enable_incremental_sync:
                    new_evidence = [
                        ev for ev in state.evidence_pool
                        if ev.subtask_id == subtask.id
                    ]

                research_result = self.researcher.process(
                    question,
                    subtask,
                    all_evidence=state.evidence_pool,
                    new_evidence_only=new_evidence if new_evidence else None,
                )

                if research_result.get("success"):
                    evidence = research_result.get("evidence", [])
                    state.add_evidence(evidence)

                    if self.debug:
                        tokens_used = research_result.get("tokens_used", 0)
                        print(f"  ✓ 子任务 {subtask.id}: {len(evidence)} 证据 "
                              f"({tokens_used} tokens, "
                              f"增量: {research_result.get('incremental_used')})")

                state.mark_done(subtask.id)

            # 评估是否继续
            if self.debug:
                print(f"[Step 4.{round_id}] 证据评估...")

            analysis_result = self.critic.process(
                question, state.subtasks, state.evidence_pool
            )

            if analysis_result.get("success"):
                state.missing_points = analysis_result.get("missing_points", [])
                enough = analysis_result.get("enough", True)

                if self.debug:
                    print(f"  ✓ 证据充分: {enough}")

                if enough:
                    break

                new_subtasks = analysis_result.get("new_subtasks", [])
                if new_subtasks:
                    state.add_subtasks(new_subtasks)

        # Step 5: 生成答案
        if self.debug:
            print("[Step 5] 答案生成...")

        writing_result = self.writer.process(question, state.subtasks, state.evidence_pool)

        if writing_result.get("success"):
            state.final_answer = writing_result.get("answer", "")
            if self.debug:
                print(f"  ✓ 答案长度: {len(state.final_answer)} 字")
        else:
            state.final_answer = "无法生成答案"

        return {
            "success": True,
            "question_type": state.question_type,
            "subtasks": state.subtasks,
            "evidence_pool": state.evidence_pool,
            "final_answer": state.final_answer,
            "missing_points": state.missing_points,
            "round_id": state.round_id
        }

    def _get_optimization_stats(self) -> Dict[str, Any]:
        """
        获取优化统计信息
        """
        stats = {
            "total_turns": len(self.conversation_turns),
            "total_evidence_collected": sum(
                len(turn['result'].get('evidence_pool', []))
                for turn in self.conversation_turns
            ),
            "average_memory_usage": "N/A",
            "incremental_sync_enabled": self.enable_incremental_sync,
            "researcher_v2_used": isinstance(self.researcher, ResearcherAgentV2),
        }

        # 计算平均内存使用
        memory_stats = [
            turn['memory_stats']['memory_utilization']
            for turn in self.conversation_turns
            if 'memory_stats' in turn
        ]
        if memory_stats:
            avg = sum(
                float(m.rstrip('%')) for m in memory_stats
            ) / len(memory_stats)
            stats['average_memory_usage'] = f"{avg:.1f}%"

        return stats

    def export_session_data(self, filepath: Optional[str] = None) -> Dict[str, Any]:
        """
        导出完整的会话数据
        """
        export_data = {
            "session_id": self.session_id,
            "created_at": self.memory.created_at.isoformat(),
            "total_turns": len(self.conversation_turns),
            "conversation_turns": self.conversation_turns,
            "memory_export": self.memory.export_session(),
            "optimization_stats": self._get_optimization_stats(),
        }

        if filepath:
            import json
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
                if self.debug:
                    print(f"会话数据已导出到: {filepath}")

        return export_data

    def get_session_summary(self) -> str:
        """
        获取会话总结
        """
        if not self.conversation_turns:
            return "空会话"

        total_evidence = sum(
            len(turn['result'].get('evidence_pool', []))
            for turn in self.conversation_turns
        )

        memory_stats = self.memory.get_memory_stats()

        summary = f"""
会话总结:
  ID: {self.session_id}
  轮次: {len(self.conversation_turns)}
  总证据: {total_evidence} 条
  内存使用: {memory_stats['memory_utilization']}
  启用增量同步: {self.enable_incremental_sync}
"""
        return summary
