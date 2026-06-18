"""FastAPI 评测微服务 - 服务入口

这是方案 C 的核心：把"LLM-as-judge 评测"拆成一个独立的后端微服务，
体现"前后端分离"的架构能力。

启动方式：
    uvicorn evaluation_service.main:app --port 8001 --reload

访问交互式文档：
    http://localhost:8001/docs
"""
import sys
from pathlib import Path

# 把项目根目录加入路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from evaluation_service.models import (
    JudgeRequest,
    JudgeResponse,
    BatchJudgeRequest,
    BatchJudgeResponse,
    HealthResponse,
)
from evaluation_service.evaluator import judge_single


# 创建 FastAPI 应用
app = FastAPI(
    title="AI 评测微服务",
    description="提供 LLM-as-judge 自动评分能力的后端微服务（方案 C 的后端部分）",
    version="1.0.0",
)

# 允许跨域（Streamlit 前端调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_model=HealthResponse)
def root():
    """根路径 - 健康检查"""
    return HealthResponse()


@app.get("/health", response_model=HealthResponse)
def health():
    """健康检查接口（部署时探活用）"""
    return HealthResponse()


@app.post("/judge", response_model=JudgeResponse)
def judge(request: JudgeRequest):
    """
    单条 LLM-as-judge 评分

    输入：问题 + 回答 + 参考上下文
    输出：0-1 的得分 + 评分理由
    """
    result = judge_single(
        question=request.question,
        answer=request.answer,
        context=request.context,
        judge_model=request.judge_model,
        judge_temperature=request.judge_temperature,
    )
    return JudgeResponse(**result)


@app.post("/judge/batch", response_model=BatchJudgeResponse)
def judge_batch(request: BatchJudgeRequest):
    """
    批量 LLM-as-judge 评分

    输入：多条 (问题, 回答, 上下文)
    输出：每条的得分 + 整体平均分
    """
    results = []
    for item in request.items:
        result = judge_single(
            question=item.question,
            answer=item.answer,
            context=item.context,
            judge_model=request.judge_model,
            judge_temperature=request.judge_temperature,
        )
        results.append(JudgeResponse(**result))

    # 统计
    success_results = [r for r in results if r.success]
    success_count = len(success_results)
    avg_score = (
        sum(r.score for r in success_results) / success_count
        if success_count > 0 else 0.0
    )

    return BatchJudgeResponse(
        results=results,
        total=len(results),
        success_count=success_count,
        avg_score=avg_score,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "evaluation_service.main:app",
        host="0.0.0.0",
        port=config.EVALUATION_SERVICE_PORT,
        reload=True,
    )
