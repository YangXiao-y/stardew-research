"""
研究相关的 API 路由
POST /api/research - 启动研究
POST /api/research/turn - 单轮对话
GET /api/research/{id} - 获取研究结果
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional, List
from datetime import datetime
import uuid
import logging

from app.schemas import (
    ResearchRequest,
    ResearchResponse,
    ResearchTurnRequest,
    ResearchTurnResponse,
    ResearchStatusResponse
)
from app.services import research_service

router = APIRouter()
logger = logging.getLogger(__name__)

# 内存存储 (生产环境应使用数据库)
research_sessions = {}


@router.post("/research", response_model=ResearchResponse)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    """
    启动新的研究任务

    Args:
        request: 研究请求
        - question: 用户问题
        - model: LLM 模型 (qwen/gpt4/claude)
        - debug: 是否启用调试模式

    Returns:
        研究会话信息 (包含 session_id 和初始结果)

    Example:
        POST /api/research
        {
            "question": "第一年春季最赚钱的农作物是什么?",
            "model": "qwen",
            "debug": false
        }
    """
    try:
        # 创建会话
        session_id = str(uuid.uuid4())
        logger.info(f"📝 创建新研究会话: {session_id}")
        logger.info(f"❓ 问题: {request.question}")

        # 执行研究
        result = await research_service.execute_research(
            question=request.question,
            game=request.game,
            model=request.model,
            debug=request.debug
        )

        # 保存到内存
        research_sessions[session_id] = {
            "created_at": datetime.now(),
            "game": request.game,
            "question": request.question,
            "result": result,
            "turns": [
                {
                    "turn": 0,
                    "question": request.question,
                    "answer": result.get("final_answer", ""),
                    "timestamp": datetime.now()
                }
            ]
        }

        logger.info(f"✅ 研究完成: {session_id}")

        return ResearchResponse(
            session_id=session_id,
            game=request.game,
            question=request.question,
            question_type=result.get("question_type", "general_qa"),
            subtasks_count=result.get("subtasks_count", 3),
            evidence_count=result.get("evidence_count", 5),
            answer=result.get("final_answer", ""),
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"❌ 研究失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research/turn", response_model=ResearchTurnResponse)
async def research_turn(request: ResearchTurnRequest):
    """
    单轮对话 (用于多轮对话场景)

    Args:
        request:
        - session_id: 会话 ID (如果为空则创建新会话)
        - question: 当前问题
        - model: LLM 模型
        - use_memory: 是否使用历史上下文

    Returns:
        单轮对话结果

    Example:
        POST /api/research/turn
        {
            "session_id": "uuid-xxx",
            "question": "这些农作物的生长周期是多少?",
            "model": "qwen",
            "use_memory": true
        }
    """
    try:
        # 处理会话
        session_id = request.session_id or str(uuid.uuid4())

        if session_id not in research_sessions:
            research_sessions[session_id] = {
                "created_at": datetime.now(),
                "game": request.game or "Stardew Valley",
                "turns": []
            }

        session = research_sessions[session_id]
        session_game = request.game or session.get("game", "Stardew Valley")
        session["game"] = session_game
        turn_num = len(session["turns"]) + 1

        logger.info(f"🔄 处理轮次 {turn_num}: {session_id}")
        logger.info(f"❓ 问题: {request.question}")

        # 获取历史上下文 (如启用)
        previous_context = ""
        if request.use_memory and len(session["turns"]) > 0:
            previous_turn = session["turns"][-1]
            previous_context = f"前一轮讨论: {previous_turn['question']}"
            logger.info(f"📚 使用历史记忆: {previous_turn['question'][:50]}...")

        # 执行研究
        result = await research_service.execute_research(
            question=request.question,
            game=session_game,
            model=request.model,
            debug=request.debug
        )

        # 保存轮次
        session["turns"].append({
            "turn": turn_num,
            "question": request.question,
            "answer": result.get("final_answer", ""),
            "evidence_count": len(result.get("evidence_pool", [])),
            "timestamp": datetime.now()
        })

        logger.info(f"✅ 轮次 {turn_num} 完成")

        return ResearchTurnResponse(
            session_id=session_id,
            turn=turn_num,
            game=session_game,
            question=request.question,
            answer=result.get("final_answer", ""),
            evidence_count=len(result.get("evidence_pool", [])),
            used_memory=request.use_memory,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"❌ 轮次处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/research/{session_id}", response_model=ResearchStatusResponse)
async def get_research_status(session_id: str):
    """
    获取研究会话的详细信息

    Args:
        session_id: 会话 ID

    Returns:
        会话的完整数据和统计信息

    Example:
        GET /api/research/uuid-xxx
    """
    try:
        if session_id not in research_sessions:
            raise HTTPException(status_code=404, detail="会话不存在")

        session = research_sessions[session_id]

        return ResearchStatusResponse(
            session_id=session_id,
            created_at=session["created_at"].isoformat(),
            total_turns=len(session["turns"]),
            turns=[
                {
                    "turn": t["turn"],
                    "question": t["question"],
                    "answer_preview": t["answer"][:200] if t["answer"] else "",
                    "timestamp": t["timestamp"].isoformat()
                }
                for t in session["turns"]
            ],
            total_evidence=sum(
                t.get("evidence_count", 0) for t in session["turns"]
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取会话信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/research")
async def list_research_sessions(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    列出所有研究会话 (分页)

    Args:
        limit: 每页数量
        offset: 偏移量

    Returns:
        会话列表和总数
    """
    try:
        sessions_list = [
            {
                "session_id": sid,
                "created_at": s["created_at"].isoformat(),
                "turns": len(s["turns"]),
                "first_question": s["turns"][0]["question"] if s["turns"] else ""
            }
            for sid, s in research_sessions.items()
        ]

        # 按创建时间倒序排列
        sessions_list = sorted(
            sessions_list,
            key=lambda x: x["created_at"],
            reverse=True
        )

        # 分页
        paginated = sessions_list[offset:offset + limit]

        return {
            "total": len(sessions_list),
            "limit": limit,
            "offset": offset,
            "sessions": paginated
        }

    except Exception as e:
        logger.error(f"❌ 获取会话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/research/{session_id}")
async def delete_research_session(session_id: str):
    """
    删除研究会话

    Args:
        session_id: 会话 ID

    Returns:
        删除成功消息
    """
    try:
        if session_id not in research_sessions:
            raise HTTPException(status_code=404, detail="会话不存在")

        del research_sessions[session_id]
        logger.info(f"🗑️ 删除会话: {session_id}")

        return {
            "message": "会话已删除",
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
