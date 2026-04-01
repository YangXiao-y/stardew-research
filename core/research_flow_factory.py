"""
研究流程工厂
支持在旧版本(LangChain)和新版本(AutoGen)之间切换
"""

from enum import Enum
from typing import Optional
from core.state import ResearchState


class ResearchFlowMode(Enum):
    """研究流程模式"""
    LEGACY = "legacy"  # 原有的LangChain版本
    AUTOGEN = "autogen"  # 新的AutoGen版本


class ResearchFlowFactory:
    """研究流程工厂"""

    _default_mode = ResearchFlowMode.AUTOGEN
    _instance_cache = {}

    @classmethod
    def set_default_mode(cls, mode: ResearchFlowMode) -> None:
        """设置默认模式"""
        cls._default_mode = mode

    @classmethod
    def create_flow(
        self,
        mode: Optional[ResearchFlowMode] = None,
        model: str = "qwen",
        debug: bool = False,
    ):
        """
        创建研究流程

        Args:
            mode: 模式 (default: _default_mode)
            model: LLM模型
            debug: 调试模式

        Returns:
            研究流程实例

        Raises:
            ValueError: 如果模式未知
        """
        if mode is None:
            mode = self._default_mode

        if mode == ResearchFlowMode.LEGACY:
            from core.research_flow import DeepResearchFlow

            return DeepResearchFlow()

        elif mode == ResearchFlowMode.AUTOGEN:
            from core.autogen_research_flow import AutoGenResearchFlow

            return AutoGenResearchFlow(model=model, debug=debug)

        else:
            raise ValueError(f"Unknown mode: {mode}")

    @classmethod
    def get_available_modes(cls) -> list[str]:
        """获取可用的模式"""
        return [mode.value for mode in ResearchFlowMode]


def get_research_flow(
    mode: str = "autogen",
    model: str = "qwen",
    debug: bool = False,
):
    """
    便利函数 - 获取研究流程

    Args:
        mode: "legacy" 或 "autogen"
        model: LLM模型
        debug: 调试模式

    Returns:
        研究流程实例

    Example:
        >>> flow = get_research_flow(mode="autogen", model="qwen", debug=True)
        >>> result = flow.run("What is the best crop for spring?")
    """
    try:
        mode_enum = ResearchFlowMode(mode)
    except ValueError:
        raise ValueError(
            f"Unknown mode: {mode}. Available: {ResearchFlowFactory.get_available_modes()}"
        )

    return ResearchFlowFactory.create_flow(mode=mode_enum, model=model, debug=debug)
