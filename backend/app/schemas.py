"""
Pydantic 数据模型 (API 请求/响应)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== 研究相关 ====================

class ResearchRequest(BaseModel):
    """研究启动请求"""
    question: str = Field(..., min_length=1, description="用户问题")
    model: str = Field("qwen", description="LLM 模型 (qwen/gpt4/claude)")
    debug: bool = Field(False, description="是否启用调试模式")

    class Config:
        json_schema_extra = {
            "example": {
                "question": "第一年春季最赚钱的农作物是什么?",
                "model": "qwen",
                "debug": False
            }
        }


class ResearchResponse(BaseModel):
    """研究响应"""
    session_id: str = Field(..., description="会话 ID")
    question: str = Field(..., description="原始问题")
    question_type: str = Field(..., description="问题类型")
    subtasks_count: int = Field(..., description="子任务数")
    evidence_count: int = Field(..., description="收集的证据数")
    answer: str = Field(..., description="最终答案")
    timestamp: str = Field(..., description="回答时间戳")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "question": "第一年春季最赚钱的农作物是什么?",
                "question_type": "strategy_qa",
                "subtasks_count": 3,
                "evidence_count": 12,
                "answer": "根据我们的研究...",
                "timestamp": "2024-03-29T10:00:00"
            }
        }


class ResearchTurnRequest(BaseModel):
    """单轮对话请求"""
    session_id: Optional[str] = Field(None, description="会话 ID (为空则创建新会话)")
    question: str = Field(..., min_length=1, description="当前问题")
    model: str = Field("qwen", description="LLM 模型")
    debug: bool = Field(False, description="是否启用调试")
    use_memory: bool = Field(True, description="是否使用历史上下文")

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "question": "这些农作物的生长周期是多少?",
                "model": "qwen",
                "debug": False,
                "use_memory": True
            }
        }


class ResearchTurnResponse(BaseModel):
    """单轮对话响应"""
    session_id: str
    turn: int
    question: str
    answer: str
    evidence_count: int
    used_memory: bool
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "turn": 2,
                "question": "这些农作物的生长周期是多少?",
                "answer": "Parsnip 和 Cauliflower...",
                "evidence_count": 8,
                "used_memory": True,
                "timestamp": "2024-03-29T10:05:00"
            }
        }


class ResearchTurn(BaseModel):
    """会话中的单轮对话"""
    turn: int
    question: str
    answer_preview: str
    timestamp: str


class ResearchStatusResponse(BaseModel):
    """研究会话状态响应"""
    session_id: str
    created_at: str
    total_turns: int
    turns: List[ResearchTurn]
    total_evidence: int


# ==================== 会话相关 ====================

class SessionCreateRequest(BaseModel):
    """创建会话请求"""
    name: Optional[str] = Field(None, description="会话名称")
    description: Optional[str] = Field(None, description="会话描述")


class SessionResponse(BaseModel):
    """会话响应"""
    session_id: str
    first_question: Optional[str] = Field(None, description="第一个问题")
    name: Optional[str] = None
    description: Optional[str] = None
    created_at: str
    updated_at: Optional[str] = None
    turns: int = Field(0, description="对话轮次")
    turn_count: Optional[int] = None
    total_evidence: int = 0


class SessionListResponse(BaseModel):
    """会话列表响应"""
    total: int
    limit: int
    skip: int = Field(0, description="跳过数")
    offset: Optional[int] = None
    sessions: List[SessionResponse]


# ==================== 导出相关 ====================

class ExportRequest(BaseModel):
    """导出请求"""
    session_id: str
    format: str = Field("json", description="导出格式 (json/csv/markdown)")


class ExportResponse(BaseModel):
    """导出响应"""
    success: bool = True
    session_id: str
    format: str
    data: str = Field(..., description="导出的数据内容")
    timestamp: str
    message: Optional[str] = None
    url: Optional[str] = None
    filename: Optional[str] = None
    size: Optional[int] = None
    created_at: Optional[str] = None


# ==================== 状态相关 ====================

class ModelInfo(BaseModel):
    """模型信息"""
    name: str
    description: str
    available: bool


class EngineStats(BaseModel):
    """引擎统计"""
    total_sessions: int
    active_sessions: int
    total_research_count: Optional[int] = 0
    total_tokens_used: int
    average_response_time: float
    available_models: List[Dict[str, Any]] = []


class SystemResources(BaseModel):
    """系统资源状态"""
    cpu_percent: float
    memory_used_percent: float
    memory_available_gb: float
    disk_used_percent: float


class SystemStatus(BaseModel):
    """系统状态"""
    status: str = Field(..., description="系统状态 (operational/degraded/error)")
    timestamp: str
    version: str = "2.0.0"
    uptime_seconds: float
    available_models: Optional[List[ModelInfo]] = None
    engine_stats: Optional[EngineStats] = None
    system_resources: Optional[SystemResources] = None


# ==================== 通用响应 ====================

class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    status_code: int
    timestamp: str
    details: Optional[Dict[str, Any]] = None


class SuccessResponse(BaseModel):
    """成功响应 (通用)"""
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str
