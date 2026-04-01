"""
Skill系统基类
Skill是可复用的能力单元，包含：prompt_template, validator, retry_handler
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, ValidationError


class BaseSkillOutput(BaseModel):
    """Skill输出基类 - 所有Skill都应该返回一个BaseSkillOutput的子类"""
    success: bool
    error_message: Optional[str] = None


class BaseSkill(ABC):
    """
    Skill基类 - 可复用的能力单元

    每个Skill代表一个能力：
    - RoutingSkill: 问题分类
    - PlanningSkill: 任务拆解
    - ResearchSkill: 搜索策划
    - AnalysisSkill: 证据评估
    - WritingSkill: 答案生成
    """

    def __init__(self, name: str, description: str, output_schema: Type[BaseSkillOutput]):
        """
        初始化Skill

        Args:
            name: Skill名称
            description: Skill描述
            output_schema: Pydantic模型，定义输出结构
        """
        self.name = name
        self.description = description
        self.output_schema = output_schema

    @abstractmethod
    def generate_prompt(self, inputs: Dict[str, Any]) -> str:
        """
        生成prompt给LLM

        Args:
            inputs: 输入参数字典

        Returns:
            prompt字符串
        """
        pass

    @abstractmethod
    def parse_output(self, output: str) -> Dict[str, Any]:
        """
        解析LLM输出为结构化数据

        Args:
            output: LLM返回的字符串

        Returns:
            解析后的字典
        """
        pass

    def validate(self, output_dict: Dict[str, Any]) -> bool:
        """
        验证输出是否符合schema

        Args:
            output_dict: 输出字典

        Returns:
            True if valid
        """
        try:
            self.output_schema(**output_dict)
            return True
        except ValidationError as e:
            print(f"Validation error in {self.name}: {e}")
            return False

    def run(self, inputs: Dict[str, Any], llm_call_fn) -> BaseSkillOutput:
        """
        执行Skill

        Args:
            inputs: 输入参数
            llm_call_fn: LLM调用函数，接收prompt，返回response

        Returns:
            BaseSkillOutput: 结构化输出
        """
        try:
            # 生成prompt
            prompt = self.generate_prompt(inputs)

            # 调用LLM
            response = llm_call_fn(prompt)

            # 解析输出
            output_dict = self.parse_output(response)

            # 验证输出
            if not self.validate(output_dict):
                return self.output_schema(
                    success=False,
                    error_message=f"Output validation failed for {self.name}",
                )

            # 创建输出对象
            output_obj = self.output_schema(**output_dict)
            return output_obj

        except Exception as e:
            return self.output_schema(
                success=False,
                error_message=f"Skill execution failed: {str(e)}",
            )

    def get_info(self) -> Dict[str, Any]:
        """获取Skill信息"""
        return {
            "name": self.name,
            "description": self.description,
            "output_schema": self.output_schema.__name__,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"


class SkillChain:
    """
    Skill链 - 按照指定顺序执行多个Skills
    """

    def __init__(self, skills: list[BaseSkill], name: str = "SkillChain"):
        self.skills = skills
        self.name = name
        self.results = {}

    def add_skill(self, skill: BaseSkill) -> None:
        """添加Skill"""
        self.skills.append(skill)

    def run(self, initial_inputs: Dict[str, Any], llm_call_fn) -> Dict[str, Any]:
        """
        按顺序执行Skills

        Args:
            initial_inputs: 初始输入
            llm_call_fn: LLM调用函数

        Returns:
            最后一个Skill的输出
        """
        current_output = initial_inputs

        for skill in self.skills:
            print(f"Executing Skill: {skill.name}")

            # 如果skill需要之前的结果，合并输入
            skill_input = {**current_output}

            # 执行skill
            result = skill.run(skill_input, llm_call_fn)
            self.results[skill.name] = result

            # 准备下一个skill的输入
            if hasattr(result, "dict"):
                current_output = result.dict()
            else:
                current_output = {"result": result}

        return current_output

    def get_results(self) -> Dict[str, Any]:
        """获取所有skill的执行结果"""
        return self.results

    def __repr__(self) -> str:
        skills_str = ", ".join([s.name for s in self.skills])
        return f"<SkillChain: {skills_str}>"
