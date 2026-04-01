"""
AutoGen 配置文件
支持多个LLM模型和Agent配置
"""

import os
from typing import Dict, Any

# LLM 模型配置
LLM_CONFIG = {
    "qwen": {
        "model": "qwen-plus",
        "api_key": os.getenv("QWEN_API_KEY", ""),
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_type": "qwen"
    },
    "gpt4": {
        "model": "gpt-4",
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "base_url": "https://api.openai.com/v1",
        "api_type": "openai"
    },
    "claude": {
        "model": "claude-3-opus-20240229",
        "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
        "api_type": "anthropic"
    }
}

# AutoGen Agent 配置
AUTOGEN_CONFIG = {
    "cache_seed": 42,
    "temperature": 0.7,
    "timeout": 60,
    "max_consecutive_auto_reply": 10,
}

# Agent 角色和提示词模板
AGENT_PROMPTS = {
    "router": """你是一个智能问题分类专家。
根据用户提问，分析问题的类型并制定研究方向。
问题类型包括：
- deep_research: 需要深入调查和多个信息源
- strategy_qa: 需要规划和策略分析
- knowledge_qa: 需要专业知识回答

输出格式：
{type: "问题类型", reasoning: "分类理由"}""",

    "planner": """你是一个任务拆解专家。
根据问题和问题类型，将其拆解为具体的研究子任务。
确保子任务清晰、可执行并覆盖问题的各个方面。

输出格式：
{
  "main_question": "主问题",
  "subtasks": [
    {"task_id": 1, "description": "子任务描述", "priority": "high/medium/low"},
    ...
  ]
}""",

    "researcher": """你是一个信息检索和综合专家。
根据分配的子任务，进行网络搜索和信息收集。
你可以使用搜索工具找到相关信息。
评估信息的相关性和可信度。

输出格式：
{
  "task_id": 1,
  "findings": [
    {"source": "来源", "content": "内容摘要", "relevance": 0.8},
    ...
  ],
  "summary": "发现总结"
}""",

    "critic": """你是一个信息质量评估专家。
评估已收集的证据质量、完整性和矛盾之处。
识别需要进一步调查的缺口。
判断是否有足够的信息来回答原始问题。

输出格式：
{
  "evidence_quality": "high/medium/low",
  "completeness": 0.85,
  "gaps": ["缺口1", "缺口2"],
  "ready_for_answer": true/false,
  "next_steps": "建议的后续步骤"
}""",

    "writer": """你是一个专业的答案生成专家。
根据所有收集的信息和证据，生成一个全面、准确、结构清晰的答案。
确保：
- 回答直接明了
- 包含支持证据
- 逻辑清晰连贯
- 避免矛盾信息

输出格式：
{
  "answer": "完整的答案内容",
  "confidence": 0.9,
  "sources_used": ["来源1", "来源2"],
  "evidence_summary": "证据摘要"
}"""
}

def get_llm_config(model_name: str = "qwen") -> Dict[str, Any]:
    """获取LLM配置"""
    return LLM_CONFIG.get(model_name, LLM_CONFIG["qwen"])

def get_agent_prompt(agent_role: str) -> str:
    """获取Agent提示词"""
    return AGENT_PROMPTS.get(agent_role, "")
