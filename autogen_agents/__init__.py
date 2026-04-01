"""
AutoGen Agents 综合模块
包含所有核心Agent和工厂方法
"""

from autogen_agents.base_agent import BaseAutoGenAgent
from autogen_agents.router_agent import RouterAgent
from autogen_agents.planner_agent import PlannerAgent
from autogen_agents.researcher_agent import ResearcherAgent
from autogen_agents.critic_agent import CriticAgent
from autogen_agents.writer_agent import WriterAgent


def create_agent(agent_type: str, model: str = "qwen") -> BaseAutoGenAgent:
    """
    工厂方法 - 根据类型创建Agent

    Args:
        agent_type: "router", "planner", "researcher", "critic", "writer"
        model: 使用的模型

    Returns:
        对应的Agent实例

    Raises:
        ValueError: 如果agent_type未知
    """
    agents_map = {
        "router": RouterAgent,
        "planner": PlannerAgent,
        "researcher": ResearcherAgent,
        "critic": CriticAgent,
        "writer": WriterAgent,
    }

    if agent_type not in agents_map:
        raise ValueError(
            f"Unknown agent type: {agent_type}. "
            f"Available: {list(agents_map.keys())}"
        )

    return agents_map[agent_type](model=model)


def create_all_agents(model: str = "qwen") -> dict:
    """
    创建所有Agent

    Args:
        model: 使用的模型

    Returns:
        包含所有Agent的字典
    """
    return {
        "router": RouterAgent(model=model),
        "planner": PlannerAgent(model=model),
        "researcher": ResearcherAgent(model=model),
        "critic": CriticAgent(model=model),
        "writer": WriterAgent(model=model),
    }


__all__ = [
    "BaseAutoGenAgent",
    "RouterAgent",
    "PlannerAgent",
    "ResearcherAgent",
    "CriticAgent",
    "WriterAgent",
    "create_agent",
    "create_all_agents",
]
