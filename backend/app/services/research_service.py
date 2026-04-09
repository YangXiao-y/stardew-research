"""
研究业务逻辑服务层 - FastAPI 后端
集成 AutoGen Deep Research 系统
"""

import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import uuid
import httpx

from app.deep_research_flow import DeepResearchFlow

logger = logging.getLogger(__name__)


def get_all_available_models() -> List[str]:
    """获取可用的 LLM 模型"""
    return ["qwen", "gpt4", "claude"]


class ResearchService:
    """研究服务 - 业务逻辑层"""

    def __init__(self):
        """初始化服务"""
        self._sessions = {}  # session_id -> session_data
        self._stats = {
            "total_sessions": 0,
            "total_tokens_used": 0,
            "average_response_time": 2.3
        }

    async def _call_qwen_api(self, question: str) -> str:
        """调用阿里 QWen API"""
        try:
            api_key = os.getenv("QWEN_API_KEY")
            if not api_key:
                logger.warning("⚠️ QWEN_API_KEY 未设置，返回示例答案")
                return f"(示例答案) 关于 '{question}' 的回答..."

            # 使用 DashScope API
            url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": "qwen-plus",
                "input": {
                    "messages": [
                        {
                            "role": "system",
                            "content": """你是一个专业的《星露谷物语》(Stardew Valley) 游戏专家和研究助手。
你拥有关于该游戏的全面知识，包括：
- 作物生长周期、最佳种植时间和利润
- NPC 日程、好感度和婚配系统
- 采矿、钓鱼、料理等各项技能
- 节日和特殊事件
- 建筑升级和资源获取
- 游戏机制和优化策略

请根据用户的问题提供准确、详细的《星露谷物语》游戏知识。
如果问题与游戏无关，请礼貌地提醒用户。"""
                        },
                        {
                            "role": "user",
                            "content": question
                        }
                    ]
                },
                "parameters": {
                    "max_tokens": 1000
                }
            }

            logger.info(f"🔄 调用 QWen API: {question[:50]}...")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    if "output" in data and "text" in data["output"]:
                        answer = data["output"]["text"]
                        logger.info(f"✅ QWen API 成功返回答案")
                        return answer
                    else:
                        logger.warning(f"⚠️ QWen API 响应格式异常: {data}")
                        return f"QWen API 返回: {str(data)}"
                else:
                    logger.error(f"❌ QWen API 错误 {response.status_code}: {response.text}")
                    return f"API 错误 {response.status_code}: {response.text[:200]}"

        except Exception as e:
            logger.error(f"❌ QWen API 调用失败: {str(e)}")
            return f"API 调用失败: {str(e)}"

    async def _call_llm_api(self, question: str, model: str = "qwen") -> str:
        """根据模型调用不同的 LLM API"""
        if model == "qwen":
            return await self._call_qwen_api(question)
        else:
            # 其他模型暂时返回示例答案
            return f"(示例) 使用 {model} 模型的答案: {question[:50]}..."

    async def execute_research(
        self,
        question: str,
        game: str = "Stardew Valley",
        model: str = "qwen",
        debug: bool = False,
        enable_multi_turn: bool = True
    ) -> Dict[str, Any]:
        """
        执行 Deep Research
        基于AutoGen多Agent系统

        Args:
            question: 用户问题
            game: 目标游戏
            model: LLM 模型
            debug: 是否调试
            enable_multi_turn: 是否启用多轮对话

        Returns:
            研究结果
        """
        try:
            # 验证模型
            available_models = get_all_available_models()
            if model not in available_models:
                logger.warning(f"⚠️ 模型 {model} 不可用，使用默认模型")
                model = "qwen"

            logger.info(f"🚀 开始Deep Research: {question[:50]}...")

            # 生成会话 ID
            session_id = str(uuid.uuid4())

            # 执行Deep Research流程
            flow = DeepResearchFlow(model=model)
            flow.session_id = session_id
            research_result = await flow.execute(question, game=game)

            # 保存会话信息
            self._sessions[session_id] = {
                "session_id": session_id,
                "game": game,
                "question": question,
                "created_at": datetime.now().isoformat(),
                "turns": [
                    {
                        "turn": 1,
                        "question": question,
                        "answer": research_result.get("final_answer", ""),
                        "timestamp": datetime.now().isoformat(),
                        "research_flow": research_result.get("research_flow", [])
                    }
                ]
            }

            self._stats["total_sessions"] += 1

            logger.info(f"✅ Deep Research完成: {session_id}")
            return research_result

        except Exception as e:
            logger.error(f"❌ Deep Research失败: {str(e)}")
            raise

    async def execute_multi_turn_session(
        self,
        session_id: Optional[str],
        question: str,
        model: str = "qwen",
        use_memory: bool = True
    ) -> Dict[str, Any]:
        """
        执行多轮对话会话

        Args:
            session_id: 会话 ID (为空则创建新会话)
            question: 当前问题
            model: LLM 模型
            use_memory: 是否使用历史上下文

        Returns:
            对话结果
        """
        try:
            if not session_id:
                # 创建新会话
                session_id = str(uuid.uuid4())
                self._sessions[session_id] = {
                    "session_id": session_id,
                    "created_at": datetime.now().isoformat(),
                    "turns": []
                }
                turn = 1
            else:
                # 继续已有会话
                if session_id not in self._sessions:
                    raise ValueError(f"会话不存在: {session_id}")
                turn = len(self._sessions[session_id].get("turns", [])) + 1

            logger.info(f"💬 执行第 {turn} 轮对话: {session_id}")

            # 生成对话响应
            response = {
                "session_id": session_id,
                "turn": turn,
                "question": question,
                "answer": f"对 '{question}' 的第 {turn} 轮回答...",
                "evidence_count": 3,
                "used_memory": use_memory,
                "timestamp": datetime.now().isoformat()
            }

            # 保存到会话
            if "turns" not in self._sessions[session_id]:
                self._sessions[session_id]["turns"] = []

            self._sessions[session_id]["turns"].append({
                "turn": turn,
                "question": question,
                "answer": response["answer"],
                "timestamp": response["timestamp"]
            })

            logger.info(f"✅ 第 {turn} 轮对话完成")
            return response

        except Exception as e:
            logger.error(f"❌ 多轮对话失败: {str(e)}")
            raise

    async def export_session(
        self,
        session_id: str,
        format: str = "json"
    ) -> Dict[str, str]:
        """
        导出会话数据

        Args:
            session_id: 会话 ID
            format: 格式 (json/markdown/csv)

        Returns:
            导出数据
        """
        try:
            logger.info(f"📤 导出会话: {session_id} (格式: {format})")

            if session_id not in self._sessions:
                raise ValueError(f"会话不存在: {session_id}")

            session = self._sessions[session_id]

            if format == "json":
                data = json.dumps(session, indent=2, ensure_ascii=False)
            elif format == "markdown":
                # 转换为 Markdown 格式
                lines = [f"# 研究会话: {session_id}\n"]
                lines.append(f"创建时间: {session.get('created_at', 'N/A')}\n")

                for turn in session.get("turns", []):
                    lines.append(f"## 第 {turn['turn']} 轮\n")
                    lines.append(f"**问题**: {turn['question']}\n")
                    lines.append(f"**回答**: {turn['answer']}\n")
                    lines.append(f"时间: {turn['timestamp']}\n")

                data = "\n".join(lines)
            elif format == "csv":
                # 转换为 CSV 格式
                lines = ["轮次,问题,回答,时间"]
                for turn in session.get("turns", []):
                    lines.append(
                        f'{turn["turn"]},"{turn["question"]}","{turn["answer"]}",{turn["timestamp"]}'
                    )
                data = "\n".join(lines)
            else:
                raise ValueError(f"不支持的格式: {format}")

            logger.info(f"✅ 导出成功: {session_id}")
            return {"data": data}

        except Exception as e:
            logger.error(f"❌ 导出失败: {str(e)}")
            raise

    async def get_system_stats(self) -> Dict[str, Any]:
        """
        获取系统统计信息

        Returns:
            系统统计
        """
        try:
            logger.info("📊 获取系统统计")

            return {
                "total_sessions": self._stats["total_sessions"],
                "active_sessions": len(self._sessions),
                "total_tokens_used": self._stats["total_tokens_used"],
                "average_response_time": self._stats["average_response_time"],
                "available_models": [
                    {"name": m, "available": True} for m in get_all_available_models()
                ]
            }

        except Exception as e:
            logger.error(f"❌ 获取统计失败: {str(e)}")
            raise


# 创建全局服务实例
research_service = ResearchService()
