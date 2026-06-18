"""FastAPI 评测微服务 - 数据模型定义（Pydantic）"""
from typing import List, Optional
from pydantic import BaseModel, Field


# ===== 请求模型 =====

class JudgeRequest(BaseModel):
    """单条 LLM-as-judge 评分请求"""
    question: str = Field(..., description="用户问题")
    answer: str = Field(..., description="AI 的回答")
    context: str = Field(..., description="参考上下文（检索到的文档）")
    judge_model: Optional[str] = Field(None, description="评判使用的模型，不填用默认")
    judge_temperature: Optional[float] = Field(None, description="评判温度，不填用默认")


class BatchJudgeItem(BaseModel):
    """批量评测中的单个条目"""
    question: str
    answer: str
    context: str


class BatchJudgeRequest(BaseModel):
    """批量 LLM-as-judge 评分请求"""
    items: List[BatchJudgeItem] = Field(..., description="待评测的条目列表")
    judge_model: Optional[str] = Field(None, description="评判模型")
    judge_temperature: Optional[float] = Field(None, description="评判温度")


# ===== 响应模型 =====

class JudgeResponse(BaseModel):
    """单条评分响应"""
    score: float = Field(..., description="得分（0-1）")
    raw_score: float = Field(..., description="原始得分（0-10）")
    reason: str = Field(..., description="评分理由")
    success: bool = Field(True, description="是否评测成功")
    error: Optional[str] = Field(None, description="错误信息")


class BatchJudgeResponse(BaseModel):
    """批量评分响应"""
    results: List[JudgeResponse]
    total: int = Field(..., description="总条数")
    success_count: int = Field(..., description="成功条数")
    avg_score: float = Field(..., description="平均得分（0-1）")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "ok"
    service: str = "evaluation-service"
    version: str = "1.0.0"
