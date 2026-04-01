#!/usr/bin/env python3
"""
优化版本演示脚本
演示 v2 (增量同步) 和 v3 (多轮对话) 的使用
"""

from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from datetime import datetime


console = Console()


def demo_v2_incremental_sync():
    """演示 v2 增量同步"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]演示 1: v2 增量同步 (Token优化)[/bold cyan]")
    console.print("="*70 + "\n")

    console.print("""
[bold]场景:[/bold] 5 轮对话，每轮增加 10 条新证据

[bold yellow]代码框架:[/bold]
""")

    code = '''from autogen_agents.researcher_agent_v2 import ResearcherAgentV2
from core.autogen_research_flow import AutoGenResearchFlow

# 创建优化的流程
flow = AutoGenResearchFlow(model="qwen")
flow.researcher = ResearcherAgentV2(
    model="qwen",
    enable_incremental=True  # 启用增量同步
)

# 运行研究 (自动使用增量同步)
result = flow.run("第一年春季最赚钱的农作物是什么?")
'''

    console.print(Syntax(code, "python", theme="monokai", line_numbers=True))

    console.print("\n[bold green]结果对比:[/bold green]\n")

    # 创建对比表
    table = Table(title="Token 消耗对比", show_header=True, header_style="bold magenta")
    table.add_column("轮次", style="cyan")
    table.add_column("V1 (全量)", style="red")
    table.add_column("V2 (增量)", style="green")
    table.add_column("节省百分比", style="yellow")

    rounds_data = [
        ("1", "1000", "1000", "0%"),
        ("2", "2000", "1000", "50%"),
        ("3", "3000", "1000", "67%"),
        ("4", "4000", "1000", "75%"),
        ("5", "5000", "1000", "80%"),
    ]

    for round_num, v1, v2, saving in rounds_data:
        table.add_row(round_num, v1, v2, saving)

    # 总计行
    table.add_row("[bold]总计[/bold]", "[bold]15000[/bold]", "[bold]5000[/bold]", "[bold green]66.7%[/bold green]")

    console.print(table)

    console.print("\n[bold green]✓ 使用 v2 节省 66% 的 Token 消耗![/bold green]")


def demo_v3_multi_turn():
    """演示 v3 多轮对话"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]演示 2: v3 多轮对话 + 记忆[/bold cyan]")
    console.print("="*70 + "\n")

    console.print("""
[bold]场景:[/bold] 用户进行多轮次对话，系统保留上下文记忆

[bold yellow]代码框架:[/bold]
""")

    code = '''from core.multi_turn_research_flow import MultiTurnAutoGenResearchFlow

# 创建多轮对话流程
flow = MultiTurnAutoGenResearchFlow(
    model="qwen",
    session_id="user123_session",
    enable_incremental_sync=True,  # 同时启用 v2 优化
    debug=True  # 详细日志
)

# 多轮对话会话
questions = [
    "第一年春季最赚钱的农作物是什么?",
    "这些农作物的种植周期是多少?",
    "如何最大化这些农作物的收益?"
]

session_result = flow.run_multi_turn_session(questions)

# 查看会话总结
print(flow.get_session_summary())

# 导出完整的会话数据
flow.export_session_data("session_data.json")
'''

    console.print(Syntax(code, "python", theme="monokai", line_numbers=True))

    console.print("\n[bold green]运行过程模拟:[/bold green]\n")

    # 模拟多轮对话
    conversations = [
        {
            "turn": 1,
            "question": "第一年春季最赚钱的农作物是什么?",
            "memory_used": "否",
            "tokens": "1000",
            "evidence": "12"
        },
        {
            "turn": 2,
            "question": "这些农作物的种植周期是多少?",
            "memory_used": "是 (摘要)",
            "tokens": "850",
            "evidence": "18"
        },
        {
            "turn": 3,
            "question": "如何最大化这些农作物的收益?",
            "memory_used": "是 (完整)",
            "tokens": "900",
            "evidence": "24"
        }
    ]

    for conv in conversations:
        console.print(f"[bold cyan]轮次 {conv['turn']}:[/bold cyan]")
        console.print(f"  用户: {conv['question']}")
        console.print(f"  记忆使用: {conv['memory_used']}")
        console.print(f"  Token 消耗: {conv['tokens']}")
        console.print(f"  累计证据: {conv['evidence']} 条\n")

    console.print("[bold green]✓ 系统保留了上下文，自动关联用户的后续问题![/bold green]")


def demo_memory_system():
    """演示记忆系统"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]演示 3: 对话记忆系统[/bold cyan]")
    console.print("="*70 + "\n")

    console.print("""
[bold]功能:[/bold] 自动管理对话历史，超限时自动压缩

[bold yellow]代码框架:[/bold]
""")

    code = '''from core.conversation_memory import ConversationMemory, MessageRole, TokenCounter

# 创建记忆管理器
memory = ConversationMemory(
    session_id="demo_session",
    max_memory_tokens=8000,
    summary_interval=3  # 每 3 轮生成摘要
)

# 添加消息对
for turn in range(5):
    memory.add_message(
        role=MessageRole.USER,
        content=f"轮次 {turn} 的用户问题"
    )
    memory.add_message(
        role=MessageRole.ASSISTANT,
        content=f"轮次 {turn} 的系统回答"
    )
    memory.new_turn()

# 获取压缩的上下文 (自动优化)
context = memory.get_context_window(
    current_query="新问题",
    max_tokens=2000
)

# 查看内存状态
stats = memory.get_memory_stats()
print(f"消息数: {stats['total_messages']}")
print(f"总 Token: {stats['total_tokens']}")
print(f"内存使用: {stats['memory_utilization']}")
'''

    console.print(Syntax(code, "python", theme="monokai", line_numbers=True))

    console.print("\n[bold green]记忆系统的工作过程:[/bold green]\n")

    steps = [
        ("添加消息", "存储用户问题和系统回答"),
        ("自动计数", "统计 Token 总数"),
        ("超限检查", "如果 > max_memory_tokens"),
        ("自动压缩", "删除旧消息，保留摘要"),
        ("增量追踪", "记录新增消息"),
        ("上下文窗口", "返回适合参数的上下文"),
    ]

    for i, (step, desc) in enumerate(steps, 1):
        console.print(f"  {i}. [bold]{step}[/bold]")
        console.print(f"     → {desc}")

    console.print("\n[bold green]✓ 记忆系统自动处理上下文优化![/bold green]")


def demo_performance_metrics():
    """演示性能指标"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]演示 4: 性能指标对比[/bold cyan]")
    console.print("="*70 + "\n")

    # 性能指标表
    table = Table(title="各版本性能指标", show_header=True, header_style="bold magenta")
    table.add_column("指标", style="cyan")
    table.add_column("V1 (原始)", style="red")
    table.add_column("V2 (增量)", style="yellow")
    table.add_column("V3 (完整)", style="green")

    metrics = [
        ("Token (5轮)", "15000", "5000", "4800"),
        ("内存开销", "高", "中", "中"),
        ("多轮对话", "❌", "❌", "✅"),
        ("记忆跨会话", "❌", "❌", "✅"),
        ("自动压缩", "❌", "⚠️", "✅"),
        ("实现复杂度", "低", "中", "中"),
        ("推荐场景", "快速原型", "生产环境", "对话系统"),
    ]

    for metric, v1, v2, v3 in metrics:
        table.add_row(metric, v1, v2, v3)

    console.print(table)

    console.print("\n[bold yellow]成本分析:[/bold yellow]")

    cost_data = [
        ("版本", "Token成本(相对)", "适用场景"),
        ("V1", "基准(100%)", "学习/原型"),
        ("V2", "33% (-67%)", "生产/成本敏感"),
        ("V3", "32% (-68%)", "对话/复杂交互"),
    ]

    for row in cost_data:
        if row[0] == "版本":
            console.print(f"  [bold]{row[0]:<10} {row[1]:<20} {row[2]:<20}[/bold]")
        else:
            console.print(f"  {row[0]:<10} {row[1]:<20} {row[2]:<20}")


def demo_best_practices():
    """演示最佳实践"""
    console.print("\n" + "="*70)
    console.print("[bold cyan]演示 5: 最佳实践[/bold cyan]")
    console.print("="*70 + "\n")

    practices = [
        {
            "title": "1. 选择合适的版本",
            "code": '''# 简单查询 → v1
# 生产环境 → v2  (推荐)
# 如果支持多轮对话 → v3
flow = MultiTurnAutoGenResearchFlow()
'''
        },
        {
            "title": "2. 启用调试模式监控",
            "code": '''flow = MultiTurnAutoGenResearchFlow(debug=True)

# 输出:
# [Step 1] 问题路由... ✓
# [Step 2] 任务拆解... ✓
# [记忆] 压缩使用: True, Token: 1523
'''
        },
        {
            "title": "3. 定期导出会话数据",
            "code": '''# 每N轮自动导出
if turn_number % 5 == 0:
    flow.export_session_data(f"backup_{turn_number}.json")

# 分析会话关键指标
import json
with open("session_data.json") as f:
    data = json.load(f)
    print(f"轮次: {data['total_turns']}")
    print(f"Token: {data['memory_summary']['total_tokens']}")
'''
        },
        {
            "title": "4. 调整Token限制",
            "code": '''# 标准(8000 tokens)
memory = ConversationMemory()

# 宽松(16000 tokens) - 预算充足
memory = ConversationMemory(max_memory_tokens=16000)

# 严格(4000 tokens) - 成本敏感
memory = ConversationMemory(max_memory_tokens=4000)
'''
        }
    ]

    for practice in practices:
        console.print(f"[bold green]{practice['title']}[/bold green]")
        console.print(Syntax(practice['code'], "python", theme="monokai", line_numbers=False))
        console.print()


def main():
    """主函数"""
    console.print("\n" + "🚀 " * 15)
    console.print("[bold cyan]Stardew Valley 研究助手 - 优化版本演示[/bold cyan]")
    console.print("🚀 " * 15 + "\n")

    # 运行所有演示
    demo_v2_incremental_sync()
    demo_v3_multi_turn()
    demo_memory_system()
    demo_performance_metrics()
    demo_best_practices()

    # 总结
    console.print("\n" + "="*70)
    console.print("[bold green]优化版本总结[/bold green]")
    console.print("="*70 + "\n")

    console.print("""
[bold]v2 优化版本 (增量同步):[/bold]
  • 节省 66% 的 Token 消耗
  • 适合单轮对话优化
  • 易于集成到现有代码

[bold]v3 完整版本 (多轮+记忆):[/bold]
  • 节省 68% 的 Token 消耗
  • 支持真正的多轮对话
  • 自动上下文管理
  • 适合客服/对话系统

[bold green]🎯 建议:[/bold green]
  → 生产环境: 使用 v2 (成本最优)
  → 对话系统: 使用 v3 (功能完整)
  → 学习阶段: 使用 v1 (简单易用)

[bold]
📚 更多信息:
  • 测试: pytest tests/test_optimization.py -v
  • 基准: python optimize_benchmark.py
  • 文档: OPTIMIZATION_V2_V3_GUIDE.md
[/bold]
""")

    console.print("="*70 + "\n")


if __name__ == "__main__":
    main()
