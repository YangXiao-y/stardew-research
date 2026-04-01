"""
Skill系统综合模块
包含所有核心Skills和工厂方法
"""

from typing import Dict
from skills.base_skill import BaseSkill, BaseSkillOutput, SkillChain
from skills.routing_skill import RoutingSkill, RoutingSkillOutput
from skills.planning_skill import PlanningSkill, PlanningSkillOutput
from skills.research_skill import ResearchSkill, ResearchSkillOutput
from skills.analysis_skill import AnalysisSkill, AnalysisSkillOutput
from skills.writing_skill import WritingSkill, WritingSkillOutput


# 所有可用的Skills
ALL_SKILLS = [
    RoutingSkill,
    PlanningSkill,
    ResearchSkill,
    AnalysisSkill,
    WritingSkill,
]


def create_research_skill_chain() -> SkillChain:
    """
    创建研究用的Skill链

    链的顺序：Routing → Planning → (在循环中使用 Research & Analysis) → Writing
    """
    skills = [
        RoutingSkill(),
        PlanningSkill(),
    ]
    return SkillChain(skills, name="ResearchPipeline")


def create_skill(skill_name: str) -> BaseSkill:
    """
    工厂方法 - 根据名称创建Skill

    Args:
        skill_name: "routing", "planning", "research", "analysis", "writing"

    Returns:
        对应的Skill实例

    Raises:
        ValueError: 如果skill_name未知
    """
    skills_map = {
        "routing": RoutingSkill,
        "planning": PlanningSkill,
        "research": ResearchSkill,
        "analysis": AnalysisSkill,
        "writing": WritingSkill,
    }

    if skill_name not in skills_map:
        raise ValueError(f"Unknown skill: {skill_name}. Available: {list(skills_map.keys())}")

    return skills_map[skill_name]()


def get_all_skills() -> Dict[str, BaseSkill]:
    """获取所有已创建的Skills"""
    return {
        "routing": RoutingSkill(),
        "planning": PlanningSkill(),
        "research": ResearchSkill(),
        "analysis": AnalysisSkill(),
        "writing": WritingSkill(),
    }


__all__ = [
    "BaseSkill",
    "BaseSkillOutput",
    "SkillChain",
    "RoutingSkill",
    "RoutingSkillOutput",
    "PlanningSkill",
    "PlanningSkillOutput",
    "ResearchSkill",
    "ResearchSkillOutput",
    "AnalysisSkill",
    "AnalysisSkillOutput",
    "WritingSkill",
    "WritingSkillOutput",
    "create_research_skill_chain",
    "create_skill",
    "get_all_skills",
    "ALL_SKILLS",
]
