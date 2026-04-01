"""
优化版本的集成测试
测试 v2 (增量同步) 和 v3 (多轮对话) 的功能
"""

import pytest
from typing import Dict, Any
from core.conversation_memory import (
    ConversationMemory,
    TokenCounter,
    Message,
    MessageRole
)
from autogen_agents.researcher_agent_v2 import ResearcherAgentV2
from core.schemas import SubTask, EvidenceItem


class TestConversationMemory:
    """对话记忆系统测试"""

    def test_memory_creation(self):
        """测试记忆创建"""
        memory = ConversationMemory(session_id="test_session")
        assert memory is not None
        assert memory.session_id == "test_session"
        assert len(memory.messages) == 0

    def test_add_messages(self):
        """测试添加消息"""
        memory = ConversationMemory(session_id="test")

        memory.add_message(
            role=MessageRole.USER,
            content="Test question"
        )
        memory.add_message(
            role=MessageRole.ASSISTANT,
            content="Test answer"
        )

        assert len(memory.messages) == 2
        assert memory.messages[0].role == MessageRole.USER
        assert memory.messages[1].role == MessageRole.ASSISTANT

    def test_token_counter(self):
        """测试Token计数"""
        text = "这是一段测试文本"
        tokens = TokenCounter.count_tokens(text)
        assert tokens > 0

        # 较长文本应该有更多tokens
        longer_text = text * 10
        longer_tokens = TokenCounter.count_tokens(longer_text)
        assert longer_tokens > tokens

    def test_context_window_no_compression(self):
        """测试不需要压缩的上下文窗口"""
        memory = ConversationMemory(
            session_id="test",
            max_memory_tokens=10000
        )

        # 添加少量消息
        for i in range(5):
            memory.add_message(
                role=MessageRole.USER,
                content=f"Message {i}"
            )

        context = memory.get_context_window("test")
        assert context['type'] == 'full'
        assert context['compression_used'] == False
        assert len(context['messages']) == 5

    def test_context_window_with_compression(self):
        """测试需要压缩的上下文窗口"""
        memory = ConversationMemory(
            session_id="test",
            max_memory_tokens=500  # 很小的限制
        )

        # 添加大量消息
        for i in range(20):
            memory.add_message(
                role=MessageRole.USER,
                content=f"这是第 {i} 条长消息。" * 50
            )

        context = memory.get_context_window("test")
        # 应该触发压缩
        assert context['tokens_used'] <= 500 * 1.1  # 稍微超过一点

    def test_memory_stats(self):
        """测试记忆统计"""
        memory = ConversationMemory(session_id="test")

        for i in range(10):
            memory.add_message(
                role=MessageRole.USER,
                content=f"Message {i}"
            )

        stats = memory.get_memory_stats()
        assert stats['total_messages'] == 10
        assert stats['session_id'] == "test"
        assert 'memory_utilization' in stats

    def test_incremental_updates(self):
        """测试增量更新"""
        memory = ConversationMemory(session_id="test")

        # 添加5条消息
        for i in range(5):
            memory.add_message(
                role=MessageRole.USER,
                content=f"Message {i}"
            )

        # 获取增量 (应该是全部5条)
        incremental = memory.get_incremental_updates()
        assert len(incremental) == 5

        # 再获取增量 (应该是空)
        incremental2 = memory.get_incremental_updates()
        assert len(incremental2) == 0

        # 添加新消息
        memory.add_message(
            role=MessageRole.USER,
            content="New message"
        )

        # 现在应该只有1条增量
        incremental3 = memory.get_incremental_updates()
        assert len(incremental3) == 1


class TestResearcherAgentV2:
    """ResearcherAgent V2 测试"""

    def test_agent_creation(self):
        """测试Agent创建"""
        agent = ResearcherAgentV2(model="qwen", enable_incremental=True)
        assert agent is not None
        assert agent.enable_incremental == True

    def test_incremental_evidence_computation(self):
        """测试增量证据计算"""
        agent = ResearcherAgentV2(model="qwen", enable_incremental=True)

        # 创建已知的证据
        evidence1 = EvidenceItem(
            subtask_id=1,
            content="Evidence 1",
            source_type="web",
            source_url="http://example1.com",
            source_title="Source 1",
            confidence=0.8
        )
        agent.previously_seen_evidence.append(evidence1)

        # 创建新证据
        evidence2 = EvidenceItem(
            subtask_id=1,
            content="Evidence 2",
            source_type="web",
            source_url="http://example2.com",
            source_title="Source 2",
            confidence=0.9
        )

        all_evidence = [evidence1, evidence2]

        # 计算增量
        incremental = agent._compute_incremental_evidence(all_evidence)

        assert len(incremental) == 1
        assert incremental[0].source_url == "http://example2.com"

    def test_evidence_summarization_empty(self):
        """测试空证据的总结"""
        agent = ResearcherAgentV2(model="qwen")

        summary = agent._summarize_evidence_for_prompt([])

        assert summary['type'] == 'empty'
        assert summary['evidence_count'] == 0

    def test_evidence_summarization_full(self):
        """测试完整证据的总结"""
        agent = ResearcherAgentV2(model="qwen")

        # 创建小量证据
        evidence = [
            EvidenceItem(
                subtask_id=1,
                content="Short content",
                source_type="web",
                source_url="http://example.com",
                source_title="Title",
                confidence=0.8
            )
            for _ in range(3)
        ]

        summary = agent._summarize_evidence_for_prompt(evidence, max_tokens=2000)

        assert summary['type'] in ['full', 'truncated']
        assert summary['evidence_count'] == 3
        assert summary['tokens'] > 0

    def test_evidence_summarization_abstract(self):
        """测试摘要型证据总结"""
        agent = ResearcherAgentV2(model="qwen")

        # 创建大量证据
        evidence = [
            EvidenceItem(
                subtask_id=1,
                content="Medium length content. " * 100,
                source_type="web",
                source_url=f"http://example{i}.com",
                source_title=f"Title {i}",
                confidence=0.8
            )
            for i in range(30)
        ]

        summary = agent._summarize_evidence_for_prompt(evidence, max_tokens=500)

        assert summary['type'] == 'abstract'
        assert 'summary' in summary
        assert summary['tokens'] <= 600

    def test_optimization_stats(self):
        """测试优化统计"""
        agent = ResearcherAgentV2(model="qwen", enable_incremental=True)

        stats = agent.get_optimization_stats()
        assert stats['incremental_enabled'] == True
        assert 'previously_seen_evidence' in stats


class TestMultiTurnFlow:
    """多轮对话流程测试"""

    def test_multi_turn_initialization(self):
        """测试多轮对话初始化"""
        from core.multi_turn_research_flow import MultiTurnAutoGenResearchFlow

        flow = MultiTurnAutoGenResearchFlow(
            model="qwen",
            enable_incremental_sync=True
        )
        assert flow is not None
        assert flow.enable_incremental_sync == True

    def test_memory_integration(self):
        """测试内存集成"""
        from core.multi_turn_research_flow import MultiTurnAutoGenResearchFlow

        flow = MultiTurnAutoGenResearchFlow(model="qwen")
        assert flow.memory is not None
        assert len(flow.conversation_turns) == 0

    def test_session_summary(self):
        """测试会话总结"""
        from core.multi_turn_research_flow import MultiTurnAutoGenResearchFlow

        flow = MultiTurnAutoGenResearchFlow(model="qwen")

        # 空会话
        summary = flow.get_session_summary()
        assert "空会话" in summary

    def test_optimization_stats_multi_turn(self):
        """测试多轮对话优化统计"""
        from core.multi_turn_research_flow import MultiTurnAutoGenResearchFlow

        flow = MultiTurnAutoGenResearchFlow(
            model="qwen",
            enable_incremental_sync=True
        )

        stats = flow._get_optimization_stats()
        assert stats['total_turns'] == 0
        assert stats['incremental_sync_enabled'] == True
        assert stats['researcher_v2_used'] == True


class TestTokenCounter:
    """Token计数器测试"""

    def test_token_counting_english(self):
        """英文Token计数"""
        text = "Hello world this is a test"
        tokens = TokenCounter.count_tokens(text)
        assert tokens > 0
        assert tokens < 100

    def test_token_counting_chinese(self):
        """中文Token计数"""
        text = "这是一段中文文本，用来测试Token计数功能"
        tokens = TokenCounter.count_tokens(text)
        assert tokens > 0

    def test_token_counting_messages(self):
        """消息列表Token计数"""
        messages = [
            Message(role=MessageRole.USER, content="Message 1"),
            Message(role=MessageRole.ASSISTANT, content="Response 1"),
            Message(role=MessageRole.USER, content="Message 2"),
        ]

        total_tokens = TokenCounter.count_messages_tokens(messages)
        assert total_tokens > 0
        assert total_tokens == sum(
            TokenCounter.count_tokens(m.content) for m in messages
        )

    def test_token_counting_scaling(self):
        """Token计数缩放性"""
        text1 = "Short"
        text2 = "Short" * 10
        text3 = "Short" * 100

        tokens1 = TokenCounter.count_tokens(text1)
        tokens2 = TokenCounter.count_tokens(text2)
        tokens3 = TokenCounter.count_tokens(text3)

        # 应该大致成比例
        assert tokens2 > tokens1
        assert tokens3 > tokens2
        # 粗略检查: tokens2 应该接近 tokens1 * 10
        assert 5 < tokens2 / tokens1 < 15


# 性能对比测试
class TestPerformanceComparison:
    """性能对比测试"""

    def test_v1_vs_v2_token_overhead(self):
        """V1 vs V2 Token开销对比"""
        from core.conversation_memory import ConversationMemory

        # 模拟生成证据
        def create_evidence(count):
            return [
                f"Evidence {i}: content content content" * 10
                for i in range(count)
            ]

        # V1: 每次发送所有证据
        v1_tokens = 0
        all_evidence = []
        for round_id in range(5):
            new_ev = create_evidence(5)
            all_evidence.extend(new_ev)
            tokens = TokenCounter.count_tokens("".join(all_evidence))
            v1_tokens += tokens

        # V2: 只发送新证据
        v2_tokens = 0
        for round_id in range(5):
            new_ev = create_evidence(5)
            tokens = TokenCounter.count_tokens("".join(new_ev))
            v2_tokens += tokens

        # V2 应该更高效
        assert v2_tokens < v1_tokens
        ratio = v2_tokens / v1_tokens
        # 应该节省至少50%
        assert ratio < 0.6


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "--tb=short"])
