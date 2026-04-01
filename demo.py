#!/usr/bin/env python3
"""
AutoGen 优化版本演示脚本

这个脚本演示了新的AutoGen框架实现如何运行。

使用方法：
    python demo.py
"""

import sys
from typing import Optional


def demo_autogen_flow():
    """演示AutoGen版本"""
    print("\n" + "="*70)
    print("AutoGen 优化版本演示")
    print("="*70 + "\n")

    try:
        from core.autogen_research_flow import AutoGenResearchFlow
        from autogen_config import get_all_available_models

        print("目可用的模型：", get_all_available_models())
        print()

        # 创建流程实例
        flow = AutoGenResearchFlow(model="qwen", debug=True)

        # 测试问题
        test_question = "Stardew Valley中，第一年春季最赚钱的农作物是什么？"

        print(f"测试问题：{test_question}\n")

        # 执行研究
        state = flow.run(test_question)

        # 显示结果摘要
        print("\n" + "="*70)
        print("研究结果摘要")
        print("="*70)
        print(f"问题类型：{state.question_type}")
        print(f"子任务数：{len(state.subtasks)}")
        print(f"证据数：{len(state.evidence_pool)}")
        print(f"研究轮次：{state.round_id}")
        print(f"最终答案长度：{len(state.final_answer)} 字符\n")

        print("最终答案:")
        print("-" * 70)
        print(state.final_answer[:500] + "..." if len(state.final_answer) > 500 else state.final_answer)
        print("-" * 70)
        print()

        return True

    except Exception as e:
        print(f"❌ AutoGen演示失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def demo_mcp_tools():
    """演示MCP工具"""
    print("\n" + "="*70)
    print("MCP 工具系统演示")
    print("="*70 + "\n")

    try:
        from mcp_tools import initialize_mcp_tools

        # 初始化工具
        registry = initialize_mcp_tools()

        # 显示已注册的工具
        tools = registry.list_tools()
        print(f"已注册的工具数：{len(tools)}")
        for tool_name in tools:
            print(f"  ✓ {tool_name}")

        print()
        return True

    except Exception as e:
        print(f"❌ MCP工具演示失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def demo_skills():
    """演示Skills系统"""
    print("\n" + "="*70)
    print("Skills 系统演示")
    print("="*70 + "\n")

    try:
        from skills import get_all_skills

        # 获取所有Skills
        skills = get_all_skills()

        print(f"已定义的Skills数：{len(skills)}")
        for name, skill in skills.items():
            print(f"  ✓ {name}: {skill.description}")

        print()
        return True

    except Exception as e:
        print(f"❌ Skills演示失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def demo_agents():
    """演示Agents系统"""
    print("\n" + "="*70)
    print("Agents 系统演示")
    print("="*70 + "\n")

    try:
        from autogen_agents import create_all_agents

        # 创建所有Agent
        agents = create_all_agents(model="qwen")

        print(f"已创建的Agents数：{len(agents)}")
        for name, agent in agents.items():
            print(f"  ✓ {name}: {agent.description}")

        print()
        return True

    except Exception as e:
        print(f"❌ Agents演示失败：{e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "🌾 "*15)
    print("Stardew Valley Deep Research - AutoGen 优化版")
    print("🌾 "*15 + "\n")

    # 检查环境
    print("📋 环境检查:")
    print("-" * 70)

    try:
        import autogen
        print(f"  ✓ pyautogen installed")
    except ImportError:
        print(f"  ✗ pyautogen NOT installed - run 'pip install -r requirements.txt'")

    try:
        import mcp
        print(f"  ✓ mcp installed")
    except ImportError:
        print(f"  ✗ mcp NOT installed - run 'pip install -r requirements.txt'")

    try:
        from config import settings
        print(f"  ✓ Configuration loaded")
        print(f"    - QWEN_API_KEY: {'✓' if settings.QWEN_API_KEY else '✗'}")
    except Exception as e:
        print(f"  ✗ Configuration load failed: {e}")

    print()
    print("=" * 70)

    # 执行演示
    results = {
        "MCP Tools": demo_mcp_tools(),
        "Skills": demo_skills(),
        "Agents": demo_agents(),
        "AutoGen Flow": demo_autogen_flow(),
    }

    # 总结
    print("\n" + "="*70)
    print("演示总结")
    print("="*70)
    for name, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{name}: {status}")

    success_count = sum(1 for s in results.values() if s)
    total_count = len(results)
    print(f"\n总计：{success_count}/{total_count} 演示成功")

    return 0 if success_count == total_count else 1


if __name__ == "__main__":
    sys.exit(main())
