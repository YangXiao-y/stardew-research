"""
Deep Research Flow - AutoGen 多Agent协调系统
"""

import asyncio
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import httpx

from app.autogen_config import get_llm_config, get_agent_prompt, AUTOGEN_CONFIG
from app.tools import tool_manager

logger = logging.getLogger(__name__)

class DeepResearchFlow:
    """基于AutoGen的Deep Research流程"""

    def __init__(self, model: str = "qwen"):
        self.model = model
        self.llm_config = get_llm_config(model)
        self.research_history = []
        self.session_id = None

    async def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """通过LLM调用"""
        try:
            api_key = self.llm_config.get("api_key")
            if not api_key:
                logger.warning(f"⚠️ {self.model.upper()}_API_KEY 未设置")
                return "模型API密钥未配置"

            # 选择合适的API端点
            if self.model == "qwen":
                return await self._call_qwen(prompt, system_prompt)
            else:
                return f"临时答案 (使用 {self.model} 模型)"

        except Exception as e:
            logger.error(f"❌ LLM调用失败: {str(e)}")
            return f"错误: {str(e)}"

    async def _call_qwen(self, prompt: str, system_prompt: str) -> str:
        """调用QWen API"""
        url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

        headers = {
            "Authorization": f"Bearer {self.llm_config['api_key']}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": prompt
        })

        payload = {
            "model": self.llm_config["model"],
            "input": {
                "messages": messages
            },
            "parameters": {
                "max_tokens": 2000
            }
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    if "output" in data and "text" in data["output"]:
                        return data["output"]["text"]
                    else:
                        logger.error(f"⚠️ 响应格式异常: {data}")
                        return "模型响应格式错误"
                else:
                    logger.error(f"❌ API错误 {response.status_code}: {response.text}")
                    return f"API错误: {response.status_code}"
        except Exception as e:
            logger.error(f"❌ QWen调用失败: {str(e)}")
            return f"调用失败: {str(e)}"

    async def route_question(self, question: str) -> Dict[str, Any]:
        """步骤1: 问题路由和分类"""
        logger.info(f"🚀 [1/5] 路由问题: {question[:50]}...")

        system_prompt = """你是一个问题分类专家。
分析用户问题的类型。
返回JSON格式: {"type": "deep_research/strategy_qa/knowledge_qa", "reasoning": "理由"}"""

        response = await self._call_llm(question, system_prompt)

        try:
            result = json.loads(response)
        except:
            result = {
                "type": "deep_research",
                "reasoning": "复杂问题，需要深入研究"
            }

        self.research_history.append({
            "stage": "routing",
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"✅ 问题分类: {result['type']}")
        return result

    async def plan_research(self, question: str, question_type: str) -> Dict[str, Any]:
        """步骤2: 研究任务规划"""
        logger.info(f"📋 [2/5] 规划研究任务...")

        system_prompt = """你是一个任务规划专家。
根据问题，将其拆解为3-5个具体的研究子任务。
返回JSON格式: {"subtasks": [{"id": 1, "description": "...", "priority": "high"}]}"""

        response = await self._call_llm(
            f"问题类型:{question_type}\n原始问题:{question}",
            system_prompt
        )

        try:
            result = json.loads(response)
        except:
            result = {
                "subtasks": [
                    {"id": 1, "description": "搜索相关信息", "priority": "high"},
                    {"id": 2, "description": "分析关键因素", "priority": "medium"},
                    {"id": 3, "description": "综合判断", "priority": "high"}
                ]
            }

        self.research_history.append({
            "stage": "planning",
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"✅ 规划了 {len(result['subtasks'])} 个子任务")
        return result

    async def research_parallel(self, question: str, subtasks: List[Dict]) -> Dict[str, Any]:
        """步骤3: 并行研究"""
        logger.info(f"🔍 [3/5] 并行执行研究任务...")

        search_queries = [task["description"] for task in subtasks]

        # 并行搜索
        search_tasks = [
            tool_manager.search_and_scrape(query, max_pages=2)
            for query in search_queries
        ]

        all_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        research_findings = {
            "evidence": [],
            "sources": [],
            "count": 0
        }

        for i, results in enumerate(all_results):
            if isinstance(results, list):
                for result in results:
                    research_findings["evidence"].append({
                        "task": search_queries[i],
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "snippet": result.get("snippet", ""),
                        "confidence": 0.8
                    })
                    if result.get("url") not in research_findings["sources"]:
                        research_findings["sources"].append(result.get("url", ""))

        research_findings["count"] = len(research_findings["evidence"])

        self.research_history.append({
            "stage": "research",
            "result": research_findings,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"✅ 收集了 {research_findings['count']} 条证据")
        return research_findings

    async def critic_review(self, question: str, findings: Dict) -> Dict[str, Any]:
        """步骤4: 批评家评审"""
        logger.info(f"🎯 [4/5] 评估证据质量...")

        evidence_count = findings.get("count", 0)

        critique = {
            "evidence_quality": "high" if evidence_count > 5 else "medium" if evidence_count > 2 else "low",
            "completeness": min(0.95, 0.5 + (evidence_count * 0.1)),
            "ready_for_answer": evidence_count > 2,
            "gaps": [] if evidence_count > 5 else ["可能需要更多信息"],
            "confidence": 0.85 if evidence_count > 5 else 0.7
        }

        self.research_history.append({
            "stage": "criticism",
            "result": critique,
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"✅ 证据评估完成: {critique['evidence_quality']} 质量")
        return critique

    async def write_answer(self, question: str, findings: Dict, critique: Dict) -> str:
        """步骤5: 生成答案"""
        logger.info(f"✍️  [5/5] 生成最终答案...")

        # 构建Evidence摘要
        evidence_summary = "\n".join([
            f"- {e['title']}: {e['snippet'][:100]}"
            for e in findings.get("evidence", [])[:5]
        ])

        system_prompt = """你是一个专业的答案生成专家。
根据提供的证据，生成全面、准确的答案。
确保逻辑清晰，引用来源。
返回JSON格式: {"answer": "...", "confidence": 0.9}"""

        prompt = f"""
原始问题: {question}

收集的证据:
{evidence_summary}

证据评估:
- 质量: {critique.get('evidence_quality')}
- 完整度: {critique.get('completeness', 0.8)}
- 信心度: {critique.get('confidence', 0.8)}

请基于以上信息生成答案。
"""

        response = await self._call_llm(prompt, system_prompt)

        try:
            result = json.loads(response)
            answer = result.get("answer", response)
        except:
            answer = response

        self.research_history.append({
            "stage": "writing",
            "result": {"answer": answer},
            "timestamp": datetime.now().isoformat()
        })

        logger.info(f"✅ 答案生成完成")
        return answer

    async def execute(self, question: str) -> Dict[str, Any]:
        """执行完整的Deep Research流程"""
        logger.info(f"📚 开始Deep Research: {question}")

        try:
            # 步骤1: 路由
            routing_result = await self.route_question(question)

            # 步骤2: 规划
            planning_result = await self.plan_research(question, routing_result.get("type"))

            # 步骤3: 并行研究
            research_result = await self.research_parallel(
                question,
                planning_result.get("subtasks", [])
            )

            # 步骤4: 评审
            critique_result = await self.critic_review(question, research_result)

            # 步骤5: 生成答案
            final_answer = await self.write_answer(question, research_result, critique_result)

            # 汇总结果
            result = {
                "session_id": self.session_id,
                "question": question,
                "question_type": routing_result.get("type"),
                "subtasks_count": len(planning_result.get("subtasks", [])),
                "evidence_count": research_result.get("count", 0),
                "evidence_quality": critique_result.get("evidence_quality"),
                "final_answer": final_answer,
                "confidence": critique_result.get("confidence", 0.7),
                "sources": research_result.get("sources", []),
                "timestamp": datetime.now().isoformat(),
                "research_flow": self.research_history
            }

            logger.info(f"✅ Deep Research完成")
            return result

        except Exception as e:
            logger.error(f"❌ Deep Research失败: {str(e)}")
            raise
