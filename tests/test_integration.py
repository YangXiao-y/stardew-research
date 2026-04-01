"""
基本集成测试
验证AutoGen框架的核心功能
"""

import pytest
from typing import Dict, Any


class TestMCPTools:
    """MCP工具系统测试"""

    def test_tool_registry_initialization(self):
        """测试工具注册表初始化"""
        from mcp_tools import initialize_mcp_tools

        registry = initialize_mcp_tools()
        assert registry is not None

        tools = registry.list_tools()
        assert len(tools) >= 3  # 至少有3个工具

    def test_search_tool_exists(self):
        """测试搜索工具存在"""
        from mcp_tools import get_tool_registry

        registry = get_tool_registry()
        search_tool = registry.get_tool("search")
        assert search_tool is not None
        assert search_tool.name == "search"

    def test_web_reader_tool_exists(self):
        """测试网页阅读器工具存在"""
        from mcp_tools import get_tool_registry

        registry = get_tool_registry()
        reader_tool = registry.get_tool("web_reader")
        assert reader_tool is not None
        assert reader_tool.name == "web_reader"


class TestSkills:
    """Skills系统测试"""

    def test_routing_skill_creation(self):
        """测试RoutingSkill创建"""
        from skills import create_skill

        skill = create_skill("routing")
        assert skill is not None
        assert skill.name == "routing"

    def test_all_skills_available(self):
        """测试所有Skills可用"""
        from skills import get_all_skills

        skills = get_all_skills()
        assert len(skills) == 5
        assert "routing" in skills
        assert "planning" in skills
        assert "research" in skills
        assert "analysis" in skills
        assert "writing" in skills

    def test_skill_schema(self):
        """测试Skill输出Schema"""
        from skills import create_skill

        skill = create_skill("routing")
        schema = skill.output_schema
        assert schema is not None


class TestAgents:
    """Agent系统测试"""

    def test_router_agent_creation(self):
        """测试RouterAgent创建"""
        from autogen_agents import create_agent

        agent = create_agent("router", model="qwen")
        assert agent is not None
        assert agent.name == "Router"

    def test_all_agents_available(self):
        """测试所有Agents可用"""
        from autogen_agents import create_all_agents

        agents = create_all_agents(model="qwen")
        assert len(agents) == 5
        assert "router" in agents
        assert "planner" in agents
        assert "researcher" in agents
        assert "critic" in agents
        assert "writer" in agents

    def test_agent_config(self):
        """测试Agent配置"""
        from autogen_agents import create_agent

        agent = create_agent("planner", model="qwen")
        config = agent.get_config()
        assert config is not None
        assert "model" in config


class TestAutoGenFlow:
    """AutoGen流程测试"""

    def test_flow_factory_legacy_mode(self):
        """测试工厂模式 - Legacy模式"""
        from core.research_flow_factory import get_research_flow

        flow = get_research_flow(mode="legacy")
        assert flow is not None

    def test_flow_factory_autogen_mode(self):
        """测试工厂模式 - AutoGen模式"""
        from core.research_flow_factory import get_research_flow

        flow = get_research_flow(mode="autogen", model="qwen")
        assert flow is not None

    def test_autogen_flow_creation(self):
        """测试AutoGenResearchFlow创建"""
        from core.autogen_research_flow import AutoGenResearchFlow

        flow = AutoGenResearchFlow(model="qwen", debug=False)
        assert flow is not None
        assert flow.max_rounds > 0


class TestConfiguration:
    """配置系统测试"""

    def test_autogen_config(self):
        """测试AutoGen配置"""
        from autogen_config import autogen_config

        assert autogen_config is not None

    def test_available_models(self):
        """测试可用模型"""
        from autogen_config import get_all_available_models

        models = get_all_available_models()
        assert len(models) > 0
        assert "qwen" in models

    def test_get_llm_config(self):
        """测试LLM配置获取"""
        from autogen_config import get_llm_config

        config = get_llm_config("qwen")
        assert config is not None
        assert "model" in config
        assert "api_key" in config


# ==================== 集成测试 ====================


class TestIntegration:
    """集成测试 - 验证组件协作"""

    def test_components_integration(self):
        """测试所有组件是否能正确集成"""
        from mcp_tools import initialize_mcp_tools
        from skills import get_all_skills
        from autogen_agents import create_all_agents

        # 初始化所有组件
        mcp_registry = initialize_mcp_tools()
        skills = get_all_skills()
        agents = create_all_agents(model="qwen")

        # 验证所有组件都已初始化
        assert len(mcp_registry.list_tools()) >= 3
        assert len(skills) == 5
        assert len(agents) == 5

    def test_flow_info_output(self):
        """测试流程信息输出"""
        from core.autogen_research_flow import AutoGenResearchFlow

        flow = AutoGenResearchFlow(model="qwen")
        info = flow.get_info()

        assert info is not None
        assert "model" in info
        assert "max_research_rounds" in info
        assert "agents" in info
        assert len(info["agents"]) == 5


# ==================== 性能测试 ====================


class TestPerformance:
    """性能相关测试"""

    def test_skill_instantiation_speed(self):
        """测试Skill实例化速度"""
        import time
        from skills import get_all_skills

        start = time.time()
        for _ in range(10):
            skills = get_all_skills()
        end = time.time()

        # 应该在100ms内完成10次实例化
        assert (end - start) < 0.1

    def test_agent_instantiation_speed(self):
        """测试Agent实例化速度"""
        import time
        from autogen_agents import create_all_agents

        start = time.time()
        for _ in range(10):
            agents = create_all_agents(model="qwen")
        end = time.time()

        # 应该在100ms内完成10次实例化
        assert (end - start) < 0.1


if __name__ == "__main__":
    # 运行测试
    # pytest -v tests/test_integration.py
    pytest.main([__file__, "-v"])
