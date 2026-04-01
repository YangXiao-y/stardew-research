#!/usr/bin/env python3
"""
优化对比演示脚本

展示:
1. v1 (原始) vs v2 (增量同步) vs v3 (多轮+记忆) 的性能对比
2. Token消耗的具体差异
3. 内存使用的优化效果
"""

import time
from typing import List, Dict
from core.conversation_memory import TokenCounter, ConversationMemory, MessageRole


class OptimizationBenchmark:
    """优化性能评测"""

    def __init__(self):
        self.results = {}

    def benchmark_token_growth(self):
        """
        演示Token增长曲线

        场景: 5轮对话，每轮收集10条证据
        """
        print("\n" + "="*70)
        print("基准测试 1: Token增长曲线")
        print("="*70)

        # 模拟证据数据
        simulated_evidence = [
            {"title": f"Source {i}", "content": f"Evidence content {i}" * 20}
            for i in range(50)
        ]

        rounds = 5
        evidence_per_round = 10

        print("\n场景: 5 轮对话，每轮收集 10 条证据 (重复现象)\n")

        # v1: 全量法 (原始)
        print("V1 (原始 - 全量法):")
        v1_tokens = []
        total_v1 = 0
        for round_id in range(1, rounds + 1):
            # 每轮包含所有之前的证据 + 新证据
            round_evidence = simulated_evidence[:evidence_per_round * round_id]
            tokens = self._estimate_tokens_for_evidence(round_evidence)
            v1_tokens.append(tokens)
            total_v1 += tokens
            print(f"  轮 {round_id}: {tokens:5d} tokens (累计: {total_v1:6d})")

        # v2: 增量法 (只发送新增)
        print("\nV2 (增量同步 - 只发送新增):")
        v2_tokens = []
        total_v2 = 0
        for round_id in range(1, rounds + 1):
            # 只发送这一轮的新证据
            round_evidence = simulated_evidence[
                (round_id - 1) * evidence_per_round:round_id * evidence_per_round
            ]
            tokens = self._estimate_tokens_for_evidence(round_evidence)
            v2_tokens.append(tokens)
            total_v2 += tokens
            print(f"  轮 {round_id}: {tokens:5d} tokens (累计: {total_v2:6d})")

        # v3: 摘要法 (自动压缩)
        print("\nV3 (摘要压缩 - 自动优化):")
        v3_tokens = []
        total_v3 = 0
        for round_id in range(1, rounds + 1):
            if round_id == 1:
                # 第一轮发送全量
                round_evidence = simulated_evidence[:evidence_per_round]
                tokens = self._estimate_tokens_for_evidence(round_evidence)
            elif round_id <= 2:
                # 前两轮发送增量
                round_evidence = simulated_evidence[
                    (round_id - 1) * evidence_per_round:round_id * evidence_per_round
                ]
                tokens = self._estimate_tokens_for_evidence(round_evidence)
            else:
                # 之后使用摘要 + 增量
                summary_tokens = 100  # 摘要token数
                increment_tokens = self._estimate_tokens_for_evidence(
                    simulated_evidence[
                        (round_id - 1) * evidence_per_round:round_id * evidence_per_round
                    ]
                )
                tokens = summary_tokens + increment_tokens

            v3_tokens.append(tokens)
            total_v3 += tokens
            print(f"  轮 {round_id}: {tokens:5d} tokens (累计: {total_v3:6d})")

        # 总结
        print("\n" + "-"*70)
        print("总 Token 消耗:")
        print(f"  V1 (原始):    {total_v1:6d} tokens")
        print(f"  V2 (增量):    {total_v2:6d} tokens (-{(1 - total_v2/total_v1)*100:.1f}%)")
        print(f"  V3 (摘要):    {total_v3:6d} tokens (-{(1 - total_v3/total_v1)*100:.1f}%)")
        print("-"*70)

        self.results['token_growth'] = {
            'v1': {'tokens': v1_tokens, 'total': total_v1},
            'v2': {'tokens': v2_tokens, 'total': total_v2},
            'v3': {'tokens': v3_tokens, 'total': total_v3},
        }

    def benchmark_memory_efficiency(self):
        """
        演示内存效率

        场景: ConversationMemory 在不同条件下的表现
        """
        print("\n" + "="*70)
        print("基准测试 2: 内存效率")
        print("="*70 + "\n")

        # 创建记忆对象
        memory = ConversationMemory(
            session_id="benchmark",
            max_memory_tokens=8000,
            summary_interval=3
        )

        print("场景: 添加 20 条消息到记忆\n")

        # 添加消息
        messages_added = 0
        for i in range(20):
            content = f"这是第 {i+1} 条消息。" * 10
            memory.add_message(
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=content
            )
            messages_added += 1

            # 每5条消息打印一次统计
            if (i + 1) % 5 == 0:
                stats = memory.get_memory_stats()
                print(f"添加 {i+1} 条消息后:")
                print(f"  已存储消息: {stats['total_messages']}")
                print(f"  总 Token: {stats['total_tokens']}")
                print(f"  内存使用: {stats['memory_utilization']}")

        print(f"\n最终统计:")
        final_stats = memory.get_memory_stats()
        print(f"  总消息数: {final_stats['total_messages']}")
        print(f"  总摘要数: {final_stats['total_summaries']}")
        print(f"  总Token: {final_stats['total_tokens']}")
        print(f"  内存使用: {final_stats['memory_utilization']}")

        self.results['memory_efficiency'] = final_stats

    def benchmark_context_window(self):
        """
        演示上下文窗口管理

        场景: 获取不同大小的上下文窗口
        """
        print("\n" + "="*70)
        print("基准测试 3: 上下文窗口管理")
        print("="*70 + "\n")

        # 创建大量消息
        memory = ConversationMemory(session_id="context_test", max_memory_tokens=5000)

        # 添加100条消息
        print("添加 100 条消息到内存...")
        for i in range(100):
            memory.add_message(
                role=MessageRole.USER if i % 2 == 0 else MessageRole.ASSISTANT,
                content=f"消息 {i}: " + "内容" * 50
            )

        print(f"已添加 {len(memory.messages)} 条消息")

        # 测试不同大小的窗口
        window_sizes = [1000, 2000, 4000, 8000]

        print("\n获取不同大小的上下文窗口:\n")

        for size in window_sizes:
            context = memory.get_context_window(
                current_query="test query",
                max_tokens=size
            )

            print(f"窗口大小: {size:5d} tokens")
            print(f"  上下文类型: {context['type']}")
            print(f"  实际 Token: {context['tokens_used']:5d}")
            print(f"  消息数: {len(context['messages'])}")
            print(f"  压缩使用: {context['compression_used']}")
            print()

        self.results['context_window'] = window_sizes

    def benchmark_incremental_sync(self):
        """
        演示增量同步的效果
        """
        print("\n" + "="*70)
        print("基准测试 4: 增量同步机制")
        print("="*70 + "\n")

        # 模拟多轮研究
        print("场景: 5 轮研究，每轮 Researcher Agent 处理\n")

        # 生成虚拟证据
        def generate_evidence(round_num, count):
            return [
                {
                    "id": f"r{round_num}_e{i}",
                    "title": f"Round {round_num} Evidence {i}",
                    "content": f"Content for round {round_num}, evidence {i}" * 20
                }
                for i in range(count)
            ]

        v1_total = 0  # 全量法
        v2_total = 0  # 增量法

        print("每轮收集 5 条新证据:\n")

        all_evidence = []
        for round_num in range(1, 6):
            new_evidence = generate_evidence(round_num, 5)
            all_evidence.extend(new_evidence)

            # V1: 发送所有证据
            v1_tokens = self._estimate_tokens_for_evidence(all_evidence)
            v1_total += v1_tokens

            # V2: 只发送新证据
            v2_tokens = self._estimate_tokens_for_evidence(new_evidence)
            v2_total += v2_tokens

            saving = (1 - v2_tokens / v1_tokens) * 100 if v1_tokens > 0 else 0

            print(f"轮 {round_num}:")
            print(f"  V1 (全量): {v1_tokens:6d} tokens")
            print(f"  V2 (增量): {v2_tokens:6d} tokens (节省 {saving:5.1f}%)")

        print("\n" + "-"*70)
        print(f"总计:")
        print(f"  V1: {v1_total:6d} tokens")
        print(f"  V2: {v2_total:6d} tokens (节省 {(1 - v2_total/v1_total)*100:.1f}%)")
        print("-"*70)

        self.results['incremental_sync'] = {
            'v1': v1_total,
            'v2': v2_total,
            'savings': (1 - v2_total / v1_total) * 100
        }

    @staticmethod
    def _estimate_tokens_for_evidence(evidence: List[Dict]) -> int:
        """
        估算证据列表的token数
        """
        total_text = ""
        for ev in evidence:
            total_text += (
                ev.get('title', '') +
                ev.get('content', '')
            )
        return TokenCounter.count_tokens(total_text)

    def print_summary(self):
        """
        打印总结报告
        """
        print("\n" + "="*70)
        print("OPTIMIZATION BENCHMARK SUMMARY")
        print("="*70 + "\n")

        if 'token_growth' in self.results:
            tg = self.results['token_growth']
            print("Token 增长对比:")
            print(f"  V1: {tg['v1']['total']:,} tokens")
            print(f"  V2: {tg['v2']['total']:,} tokens "
                  f"(-{(1 - tg['v2']['total']/tg['v1']['total'])*100:.1f}%)")
            print(f"  V3: {tg['v3']['total']:,} tokens "
                  f"(-{(1 - tg['v3']['total']/tg['v1']['total'])*100:.1f}%)")

        if 'incremental_sync' in self.results:
            ris = self.results['incremental_sync']
            print(f"\n增量同步节省: {ris['savings']:.1f}%")

        if 'memory_efficiency' in self.results:
            me = self.results['memory_efficiency']
            print(f"\n内存效率:")
            print(f"  消息数: {me['total_messages']}")
            print(f"  总Token: {me['total_tokens']}")
            print(f"  内存使用: {me['memory_utilization']}")

        print("\n推荐:")
        print("  ✓ 对于生产环境: 使用 V2 (增量同步) 或 V3 (完整优化)")
        print("  ✓ 节省 65-70% 的 Token 消耗")
        print("  ✓ 支持真正的多轮对话")
        print("\n" + "="*70 + "\n")


def main():
    """运行所有基准测试"""
    print("\n" + "🚀 "*15)
    print("Stardew Research Assistant - 优化基准测试")
    print("🚀 "*15 + "\n")

    benchmark = OptimizationBenchmark()

    # 运行基准测试
    benchmark.benchmark_token_growth()
    benchmark.benchmark_memory_efficiency()
    benchmark.benchmark_context_window()
    benchmark.benchmark_incremental_sync()

    # 打印总结
    benchmark.print_summary()


if __name__ == "__main__":
    main()
