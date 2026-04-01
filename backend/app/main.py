"""
FastAPI 主应用入口
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
from datetime import datetime
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

# 导入路由
from app.api import research, sessions, export, status

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 应用启动/关闭事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info("🚀 Stardew Research Assistant API 启动中...")
    logger.info(f"⏰ 启动时间: {datetime.now()}")
    yield
    # 关闭
    logger.info("🛑 应用关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="Stardew Valley AI Research Assistant",
    description="AI-Powered Multi-Agent Research System",
    version="2.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)


# CORS 中间件配置 (允许前端跨域请求)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Stardew Research API"
    }


# 根路由 - API 信息
@app.get("/")
async def root():
    """API 根端点"""
    return {
        "name": "Stardew Valley AI Research Assistant",
        "version": "2.0.0",
        "description": "Multi-Agent Research System with AutoGen + MCP + Skill",
        "endpoints": {
            "docs": "/api/docs",
            "health": "/health",
            "research": "/api/research",
            "sessions": "/api/sessions",
            "export": "/api/export",
            "status": "/api/status"
        }
    }


# 注册路由
app.include_router(research.router, prefix="/api", tags=["Research"])
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(export.router, prefix="/api", tags=["Export"])
app.include_router(status.router, prefix="/api", tags=["Status"])


# 错误处理
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 异常处理"""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
