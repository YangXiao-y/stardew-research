"""
导出功能 API 路由
支持会话数据的多格式导出 (JSON, Markdown, CSV)
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.schemas import ExportRequest, ExportResponse
from app.services.research_service import research_service
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Export"])


@router.post("/export", response_model=ExportResponse)
async def export_session(
    request: ExportRequest,
    background_tasks: BackgroundTasks
) -> ExportResponse:
    """
    导出研究会话数据

    Args:
        request: 导出请求，包含session_id和格式
        background_tasks: 后台任务（可选）

    Returns:
        导出的数据
    """
    try:
        logger.info(f"📤 导出会话: {request.session_id}, 格式: {request.format}")

        # 验证格式参数
        if request.format not in ["json", "markdown", "csv"]:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的导出格式: {request.format}，仅支持 json/markdown/csv"
            )

        # 调用服务层导出
        export_data = await research_service.export_session(
            session_id=request.session_id,
            format=request.format
        )

        logger.info(f"✅ 导出成功: {request.session_id}")

        return ExportResponse(
            success=True,
            session_id=request.session_id,
            format=request.format,
            data=export_data["data"],
            timestamp=datetime.now().isoformat(),
            message=f"会话数据已导出为 {request.format.upper()} 格式"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/batch")
async def batch_export(
    session_ids: list,
    format: str = "json",
    background_tasks: BackgroundTasks = None
) -> dict:
    """
    批量导出多个会话

    Args:
        session_ids: 会话ID列表
        format: 导出格式 (json/markdown/csv)
        background_tasks: 后台任务处理

    Returns:
        批量导出结果
    """
    try:
        logger.info(f"📤 批量导出 {len(session_ids)} 个会话，格式: {format}")

        if format not in ["json", "markdown", "csv"]:
            raise HTTPException(status_code=400, detail="不支持的导出格式")

        if len(session_ids) == 0:
            raise HTTPException(status_code=400, detail="会话ID列表为空")

        if len(session_ids) > 50:
            raise HTTPException(
                status_code=400,
                detail="单次批量导出最多50个会话"
            )

        # 执行批量导出
        results = []
        for session_id in session_ids:
            try:
                export_data = await research_service.export_session(
                    session_id=session_id,
                    format=format
                )
                results.append({
                    "session_id": session_id,
                    "success": True,
                    "data": export_data["data"]
                })
            except Exception as e:
                logger.warning(f"⚠️ 导出会话 {session_id} 失败: {str(e)}")
                results.append({
                    "session_id": session_id,
                    "success": False,
                    "error": str(e)
                })

        logger.info(f"✅ 批量导出完成: {len([r for r in results if r['success']])}/{len(session_ids)} 成功")

        return {
            "success": True,
            "total": len(session_ids),
            "successful": len([r for r in results if r["success"]]),
            "format": format,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 批量导出失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{session_id}/{format}")
async def get_export(session_id: str, format: str = "json") -> dict:
    """
    直接获取导出数据（不创建文件）

    Args:
        session_id: 会话ID
        format: 导出格式

    Returns:
        导出的数据
    """
    try:
        logger.info(f"🔄 获取导出数据: {session_id}, 格式: {format}")

        if format not in ["json", "markdown", "csv"]:
            raise HTTPException(status_code=400, detail="不支持的导出格式")

        export_data = await research_service.export_session(
            session_id=session_id,
            format=format
        )

        logger.info(f"✅ 获取导出数据成功: {session_id}")

        return {
            "success": True,
            "session_id": session_id,
            "format": format,
            "data": export_data["data"],
            "timestamp": datetime.now().isoformat(),
            "file_type": f"application/{format}" if format != "markdown" else "text/markdown"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 获取导出数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
