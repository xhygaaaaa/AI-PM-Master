"""评测微服务客户端 - Streamlit 前端调用 FastAPI 后端的桥梁

设计思路（方案 C 的关键）：
- 优先调用独立的 FastAPI 微服务（体现前后端分离架构）
- 如果微服务没启动，自动降级到本地直接调用（保证可用性）

这种"优先远程、降级本地"的设计在真实生产中很常见。
"""
import sys
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config


class JudgeClient:
    """LLM-as-judge 评测客户端"""

    def __init__(self, service_url: str = None):
        """
        初始化评测客户端

        Args:
            service_url: 微服务地址，默认 http://localhost:{端口}
        """
        if service_url is None:
            service_url = f"http://localhost:{config.EVALUATION_SERVICE_PORT}"
        self.service_url = service_url.rstrip("/")

    def is_service_available(self, timeout: float = 1.0) -> bool:
        """
        检查微服务是否在线

        Args:
            timeout: 超时时间（秒）

        Returns:
            是否可用
        """
        try:
            resp = requests.get(f"{self.service_url}/health", timeout=timeout)
            return resp.status_code == 200
        except Exception:
            return False

    def judge(
        self,
        question: str,
        answer: str,
        context: str,
        judge_model: str = None,
        judge_temperature: float = None,
    ) -> dict:
        """
        评测单条回答

        优先调用微服务，失败则降级到本地调用。

        Args:
            question: 用户问题
            answer: AI 回答
            context: 参考上下文

        Returns:
            评测结果字典 {score, raw_score, reason, success, error, mode}
            mode 字段标记是 "service"（走微服务）还是 "local"（本地降级）
        """
        # 1. 优先尝试微服务
        if self.is_service_available():
            try:
                resp = requests.post(
                    f"{self.service_url}/judge",
                    json={
                        "question": question,
                        "answer": answer,
                        "context": context,
                        "judge_model": judge_model,
                        "judge_temperature": judge_temperature,
                    },
                    timeout=60,
                )
                if resp.status_code == 200:
                    result = resp.json()
                    result["mode"] = "service"
                    return result
            except Exception as e:
                print(f"⚠️ 微服务调用失败，降级到本地：{e}")

        # 2. 降级到本地调用
        from evaluation_service.evaluator import judge_single
        result = judge_single(
            question=question,
            answer=answer,
            context=context,
            judge_model=judge_model,
            judge_temperature=judge_temperature,
        )
        result["mode"] = "local"
        return result
