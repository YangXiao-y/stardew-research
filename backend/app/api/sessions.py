"""
会话管理 API 路由
处理研究会话的查询、列表、删除等操作
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.schemas import SessionResponse, SessionListResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Sessions"])

# 这是一个示例实现，实际应用应该从数据库查询
# In production, inject database service here
SESSIONS_DB = {}


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    skip: int = Query(0, ge=0, description="跳过的会话数"),
    limit: int = Query(10, ge=1, le=100, description="返回的最大会话数")
) -> SessionListResponse:
    """
    获取会话列表 (分页)

    Args:
        skip: 分页起始位置 (默认0)
        limit: 分页限制 (默认10)

    Returns:
        会话列表和总数
    """
    try:
        logger.info(f"📋 获取会话列表: skip={skip}, limit={limit}")

        # 实际应用应该从数据库查询
        all_sessions = list(SESSIONS_DB.values())
        total = len(all_sessions)

        # 分页处理
        sessions = all_sessions[skip:skip + limit]

        logger.info(f"✅ 返回 {len(sessions)} 个会话 (总计 {total})")

        return SessionListResponse(
            sessions=sessions,
            total=total,
            skip=skip,
            limit=limit
        )

    except Exception as e:
        logger.error(f"❌ 获取会话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """
    获取单个会话详情

    Args:
        session_id: 会话ID

    Returns:
        会话详情
    """
    try:
        logger.info(f"🔍 获取会话详情: {session_id}")

        if session_id not in SESSIONS_DB:
            logger.warning(f"⚠️ 会话不存在: {session_id}")
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")

        session = SESSIONS_DB[session_id]
        logger.info(f"✅ 找到会话: {session_id}")

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    """
    删除会话

    Args:
        session_id: 要删除的会话ID

    Returns:
        删除结果
    """
    try:
        logger.info(f"🗑️ 删除会话: {session_id}")

        if session_id not in SESSIONS_DB:
            logger.warning(f"⚠️ 会话不存在: {session_id}")
            raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")

        # 删除会话
        del SESSIONS_DB[session_id]

        logger.info(f"✅ 会话已删除: {session_id}")

        return {
            "success": True,
            "message": f"会话 {session_id} 已删除",
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 删除会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/history")
async def get_session_history(session_id: str) -> dict:
    """
    获取会话的对话历史

    Args:
        session_id: 会话ID

    Returns:
        对话历史列表
    """
    try:
        logger.info(f"📜 获取会话历史: {session_id}")

        if session_id not in SESSIONS_DB:
            raise HTTPException(status_code=404, detail=f"会话不存在: {session_id}")

        session = SESSIONS_DB[session_id]

        return {
            "session_id": session_id,
            "turns": session.get("turns", []),
            "turn_count": len(session.get("turns", [])),
            "created_at": session.get("created_at")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取会话历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
