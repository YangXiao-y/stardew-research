"""
系统状态 API 路由
提供系统健康检查、性能指标、模型状态等信息
"""

from fastapi import APIRouter, HTTPException
from app.services.research_service import research_service
from app.schemas import SystemStatus
import logging
from datetime import datetime
import psutil
import os

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Status"])


@router.get("/health")
async def health_check() -> dict:
    """
    健康检查端点

    Returns:
        系统健康状态
    """
    try:
        logger.info("🏥 执行健康检查")

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "2.0.0",
            "service": "Stardew Valley AI Research Assistant"
        }

    except Exception as e:
        logger.error(f"❌ 健康检查失败: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


@router.get("/status", response_model=SystemStatus)
async def get_system_status() -> SystemStatus:
    """
    获取系统状态信息

    Returns:
        详细的系统状态和统计信息
    """
    try:
        logger.info("📊 获取系统状态")

        # 获取系统统计
        system_stats = await research_service.get_system_stats()

        # 获取系统资源信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')

        # 构建响应
        status = SystemStatus(
            status="operational",
            timestamp=datetime.now().isoformat(),
            version="2.0.0",
            uptime_seconds=int(datetime.now().timestamp()),
            engine_stats={
                "total_sessions": system_stats.get("total_sessions", 0),
                "active_sessions": system_stats.get("active_sessions", 0),
                "total_tokens_used": system_stats.get("total_tokens_used", 0),
                "average_response_time": system_stats.get("average_response_time", 0.0),
                "available_models": system_stats.get("available_models", [])
            },
            system_resources={
                "cpu_percent": cpu_percent,
                "memory_used_percent": memory_info.percent,
                "memory_available_gb": round(memory_info.available / (1024**3), 2),
                "disk_used_percent": disk_info.percent
            }
        )

        logger.info(f"✅ 系统状态获取成功")
        return status

    except Exception as e:
        logger.error(f"❌ 获取系统状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/models")
async def get_models_status() -> dict:
    """
    获取可用模型状态

    Returns:
        模型列表和每个模型的状态
    """
    try:
        logger.info("🤖 获取模型状态")

        system_stats = await research_service.get_system_stats()
        available_models = system_stats.get("available_models", [])

        return {
            "available_count": len(available_models),
            "models": available_models,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ 获取模型状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/metrics")
async def get_metrics() -> dict:
    """
    获取详细的性能指标

    Returns:
        详细的性能指标数据
    """
    try:
        logger.info("📈 获取性能指标")

        system_stats = await research_service.get_system_stats()

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "sessions": {
                "total": system_stats.get("total_sessions", 0),
                "active": system_stats.get("active_sessions", 0),
            },
            "tokens": {
                "total_used": system_stats.get("total_tokens_used", 0),
                "average_response_time": system_stats.get("average_response_time", 0.0)
            },
            "system": {
                "cpu_usage": psutil.cpu_percent(interval=1),
                "memory_usage": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            }
        }

        logger.info(f"✅ 性能指标获取成功")
        return metrics

    except Exception as e:
        logger.error(f"❌ 获取性能指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/info")
async def get_system_info() -> dict:
    """
    获取系统信息和配置

    Returns:
        系统信息、环境变量等
    """
    try:
        logger.info("ℹ️ 获取系统信息")

        return {
            "application": {
                "name": "Stardew Valley AI Research Assistant",
                "version": "2.0.0",
                "environment": os.getenv("ENVIRONMENT", "development")
            },
            "python": {
                "version": os.popen("python --version").read().strip(),
            },
            "system": {
                "platform": os.uname()[0] if hasattr(os, 'uname') else 'Windows',
                "processor_count": os.cpu_count()
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"❌ 获取系统信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
