"""
对话记忆系统
支持跨轮次的上下文记忆和Token优化管理
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
import json
from dataclasses import dataclass, asdict
from enum import Enum


class MessageRole(Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """单条消息"""
    role: MessageRole
    content: str
    timestamp: datetime = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class TurnSummary:
    """轮次摘要"""
    turn_number: int
    timestamp: datetime
    user_query: str
    summary: str
    key_points: List[str]
    evidence_count: int
    question_type: str


class TokenCounter:
    """Token计数工具"""

    # 粗略计算: 1 token ≈ 4 个字符或 0.75 个单词
    CHAR_TO_TOKEN = 0.25
    WORD_TO_TOKEN = 1.33

    @staticmethod
    def count_tokens(text: str) -> int:
        """估算文本的token数"""
        # 更精确的估算: 平均每个单词3-4个字符
        word_count = len(text.split())
        char_count = len(text)

        # 使用两个算法的平均值
        tokens_by_word = int(word_count * TokenCounter.WORD_TO_TOKEN)
        tokens_by_char = int(char_count * TokenCounter.CHAR_TO_TOKEN)

        return max(tokens_by_word, tokens_by_char)

    @staticmethod
    def count_messages_tokens(messages: List[Message]) -> int:
        """计算消息列表的总token数"""
        return sum(TokenCounter.count_tokens(m.content) for m in messages)


class ConversationMemory:
    """
    对话记忆管理器

    功能:
    1. 保存完整的对话历史
    2. 自动生成轮次摘要
    3. 管理Token使用量
    4. 支持增量同步
    """

    def __init__(
        self,
        session_id: str,
        max_memory_tokens: int = 8000,
        summary_interval: int = 3
    ):
        """
        初始化记忆管理器

        Args:
            session_id: 会话ID
            max_memory_tokens: 最大内存token数（超过时自动压缩）
            summary_interval: 每N轮生成一个摘要
        """
        self.session_id = session_id
        self.max_memory_tokens = max_memory_tokens
        self.summary_interval = summary_interval

        # 存储
        self.messages: List[Message] = []
        self.turn_summaries: List[TurnSummary] = []
        self.created_at = datetime.now()

        # 状态
        self.current_turn = 0
        self.last_synced_idx = 0  # 上次同步到的消息索引

    def add_message(
        self,
        role: MessageRole,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        添加消息到记忆

        Args:
            role: 角色
            content: 内容
            metadata: 元数据
        """
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        self.messages.append(message)

        # 检查是否需要压缩
        if self._should_compress():
            self._compress_old_messages()

    def new_turn(self) -> None:
        """
        标记新的一轮开始
        """
        self.current_turn += 1

        # 每N轮生成摘要
        if self.current_turn % self.summary_interval == 0:
            self._generate_summary()

    def _generate_summary(self) -> None:
        """
        为最近的轮次生成摘要
        """
        # 获取最近的N条消息
        recent_messages = self.messages[-10:]

        if not recent_messages:
            return

        # 提取关键信息
        key_points = self._extract_key_points(recent_messages)

        # 构建摘要文本
        summary_text = self._build_summary_text(recent_messages, key_points)

        # 创建摘要对象
        summary = TurnSummary(
            turn_number=self.current_turn,
            timestamp=datetime.now(),
            user_query=self._extract_user_query(recent_messages),
            summary=summary_text,
            key_points=key_points,
            evidence_count=self._count_evidence_items(recent_messages),
            question_type=self._extract_question_type(recent_messages)
        )

        self.turn_summaries.append(summary)

    def get_context_window(
        self,
        current_query: str,
        max_tokens: int = None
    ) -> Dict[str, Any]:
        """
        获取适合当前查询的上下文窗口

        使用策略:
        1. 如果总token < max_tokens: 返回全部消息
        2. 如果总token > max_tokens: 返回摘要 + 最近消息

        Args:
            current_query: 当前查询
            max_tokens: 最大token数（None则使用实例配置）

        Returns:
            包含上下文的字典
        """
        if max_tokens is None:
            max_tokens = self.max_memory_tokens

        # 计算总token
        total_tokens = TokenCounter.count_messages_tokens(self.messages)

        if total_tokens <= max_tokens:
            # 可以返回全部消息
            return {
                "type": "full",
                "messages": self.messages,
                "tokens_used": total_tokens,
                "compression_used": False
            }

        else:
            # 需要压缩
            compressed = self._build_compressed_context(max_tokens)
            return {
                "type": "compressed",
                "messages": compressed["messages"],
                "summary": compressed["summary"],
                "tokens_used": compressed["tokens_used"],
                "compression_used": True
            }

    def get_incremental_updates(self) -> List[Message]:
        """
        获取增量更新（自上次同步后的新消息）

        用于v2的增量同步机制
        """
        new_messages = self.messages[self.last_synced_idx:]
        self.last_synced_idx = len(self.messages)
        return new_messages

    def _should_compress(self) -> bool:
        """检查是否应该压缩"""
        total_tokens = TokenCounter.count_messages_tokens(self.messages)
        return total_tokens > self.max_memory_tokens * 1.5

    def _compress_old_messages(self) -> None:
        """
        压缩旧消息
        保留最新的N条消息 + 摘要
        """
        # 保留最新的10条消息
        keep_recent = 10

        if len(self.messages) <= keep_recent:
            return

        # 对旧消息生成摘要
        old_messages = self.messages[:-keep_recent]
        summary = self._build_summary_text(old_messages, [])

        # 创建摘要消息
        summary_message = Message(
            role=MessageRole.SYSTEM,
            content=f"[早期对话摘要]\n{summary}",
            metadata={"type": "compression_summary"}
        )

        # 替换
        self.messages = [summary_message] + self.messages[-keep_recent:]

    def _build_compressed_context(self, max_tokens: int) -> Dict[str, Any]:
        """
        构建压缩的上下文
        """
        context_messages = []
        remaining_tokens = max_tokens

        # 1. 添加摘要（如果有）
        if self.turn_summaries:
            latest_summary = self.turn_summaries[-1]
            summary_text = f"[摘要] {latest_summary.summary}"
            summary_tokens = TokenCounter.count_tokens(summary_text)

            if summary_tokens < remaining_tokens:
                context_messages.append(Message(
                    role=MessageRole.SYSTEM,
                    content=summary_text,
                    metadata={"type": "summary"}
                ))
                remaining_tokens -= summary_tokens

        # 2. 添加最近的消息
        recent_messages = list(reversed(self.messages))
        for msg in recent_messages:
            msg_tokens = TokenCounter.count_tokens(msg.content)
            if msg_tokens < remaining_tokens:
                context_messages.insert(0, msg)
                remaining_tokens -= msg_tokens
            else:
                break

        total_tokens = TokenCounter.count_messages_tokens(context_messages)

        return {
            "messages": context_messages,
            "summary": self.turn_summaries[-1].summary if self.turn_summaries else "",
            "tokens_used": total_tokens
        }

    def _extract_key_points(self, messages: List[Message]) -> List[str]:
        """
        从消息中提取关键点
        """
        key_points = []

        for msg in messages:
            # 简单启发式: 长消息可能包含关键信息
            if len(msg.content) > 200:
                # 取前100个字符
                key_points.append(msg.content[:100] + "...")

        return key_points[:3]  # 最多3个关键点

    def _build_summary_text(self, messages: List[Message], key_points: List[str]) -> str:
        """
        构建摘要文本
        """
        lines = []

        # 统计信息
        lines.append(f"消息数: {len(messages)}")
        lines.append(f"时间跨度: {(messages[-1].timestamp - messages[0].timestamp).seconds}秒")

        # 关键点
        if key_points:
            lines.append("关键点:")
            for point in key_points:
                lines.append(f"  • {point}")

        return "\n".join(lines)

    def _extract_user_query(self, messages: List[Message]) -> str:
        """
        提取用户查询
        """
        for msg in messages:
            if msg.role == MessageRole.USER:
                return msg.content[:100]
        return ""

    def _extract_question_type(self, messages: List[Message]) -> str:
        """
        从消息中提取问题类型
        """
        for msg in messages:
            if "question_type" in msg.content:
                try:
                    data = json.loads(msg.content)
                    return data.get("question_type", "unknown")
                except:
                    pass
        return "unknown"

    def _count_evidence_items(self, messages: List[Message]) -> int:
        """
        计算证据数
        """
        count = 0
        for msg in messages:
            if "evidence" in msg.content.lower():
                count += msg.content.count("evidence")
        return count

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计信息
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "current_turn": self.current_turn,
            "total_messages": len(self.messages),
            "total_tokens": TokenCounter.count_messages_tokens(self.messages),
            "total_summaries": len(self.turn_summaries),
            "memory_utilization": f"{TokenCounter.count_messages_tokens(self.messages) / self.max_memory_tokens * 100:.1f}%"
        }

    def export_session(self) -> Dict[str, Any]:
        """
        导出完整的会话数据
        """
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "messages": [m.to_dict() for m in self.messages],
            "summaries": [asdict(s) for s in self.turn_summaries],
            "stats": self.get_memory_stats()
        }
