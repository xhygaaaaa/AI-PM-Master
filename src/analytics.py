"""数据分析与埋点 - 记录交互日志并统计指标"""
import json
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

import config


class Analytics:
    """数据分析与统计"""

    def __init__(self):
        """初始化分析器"""
        self.log_file = config.LOG_DIR / "interactions.jsonl"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_interaction(
        self,
        question: str,
        answer: str,
        retrieved_docs: List,
        hallucination_result: Dict,
        model: str,
        temperature: float,
        input_tokens: int,
        output_tokens: int,
        response_time: float,
        user_feedback: Optional[str] = None,
        metadata: Dict = None
    ):
        """
        记录一次交互日志

        Args:
            question: 用户问题
            answer: AI 回答
            retrieved_docs: 检索到的文档
            hallucination_result: 幻觉检测结果
            model: 使用的模型
            temperature: 温度参数
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数
            response_time: 响应时间（秒）
            user_feedback: 用户反馈（useful / not_useful / None）
            metadata: 额外的元数据
        """
        # 构建日志条目
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "retrieved_docs_count": len(retrieved_docs),
            "hallucination_score": hallucination_result.get("score"),
            "risk_level": hallucination_result.get("risk_level"),
            "model": model,
            "temperature": temperature,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "response_time": response_time,
            "user_feedback": user_feedback,
            "cost": config.get_token_cost(model, input_tokens, output_tokens),
            "metadata": metadata or {},
        }

        # 追加到 JSONL 文件
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"⚠️  日志记录失败：{e}")

    def load_logs(self, limit: int = None) -> List[Dict]:
        """
        加载交互日志

        Args:
            limit: 限制返回的条目数，None 表示全部

        Returns:
            日志列表
        """
        if not self.log_file.exists():
            return []

        logs = []
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line))
        except Exception as e:
            print(f"⚠️  日志加载失败：{e}")
            return []

        # 倒序（最新的在前）
        logs.reverse()

        if limit:
            logs = logs[:limit]

        return logs

    def get_statistics(self) -> Dict:
        """
        计算统计指标

        Returns:
            统计字典
        """
        logs = self.load_logs()

        if not logs:
            return {
                "total_interactions": 0,
                "total_cost": 0,
                "avg_response_time": 0,
                "adoption_rate": 0,
                "refusal_rate": 0,
                "low_risk_rate": 0,
                "medium_risk_rate": 0,
                "high_risk_rate": 0,
            }

        total = len(logs)

        # 基础统计
        total_cost = sum(log.get("cost", 0) for log in logs)
        total_tokens = sum(log.get("total_tokens", 0) for log in logs)
        total_response_time = sum(log.get("response_time", 0) for log in logs)

        # 用户反馈统计
        useful_count = sum(1 for log in logs if log.get("user_feedback") == "useful")
        not_useful_count = sum(1 for log in logs if log.get("user_feedback") == "not_useful")
        feedback_count = useful_count + not_useful_count

        # 风险等级统计
        risk_counts = {
            "refusal": sum(1 for log in logs if log.get("risk_level") == "refusal"),
            "low": sum(1 for log in logs if log.get("risk_level") == "low"),
            "medium": sum(1 for log in logs if log.get("risk_level") == "medium"),
            "high": sum(1 for log in logs if log.get("risk_level") == "high"),
        }

        # 计算率
        adoption_rate = useful_count / feedback_count if feedback_count > 0 else 0

        return {
            "total_interactions": total,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "avg_cost_per_interaction": total_cost / total,
            "avg_tokens_per_interaction": total_tokens / total,
            "avg_response_time": total_response_time / total,
            "adoption_rate": adoption_rate,
            "feedback_count": feedback_count,
            "useful_count": useful_count,
            "not_useful_count": not_useful_count,
            "refusal_count": risk_counts["refusal"],
            "low_risk_count": risk_counts["low"],
            "medium_risk_count": risk_counts["medium"],
            "high_risk_count": risk_counts["high"],
            "refusal_rate": risk_counts["refusal"] / total,
            "low_risk_rate": risk_counts["low"] / total,
            "medium_risk_rate": risk_counts["medium"] / total,
            "high_risk_rate": risk_counts["high"] / total,
        }

    def get_time_series(self, metric: str = "cost") -> List[Dict]:
        """
        获取时间序列数据（用于绘制趋势图）

        Args:
            metric: 指标名称（cost / tokens / response_time）

        Returns:
            时间序列列表 [{"timestamp": "...", "value": ...}, ...]
        """
        logs = self.load_logs()

        time_series = []
        for log in logs:
            value = None
            if metric == "cost":
                value = log.get("cost", 0)
            elif metric == "tokens":
                value = log.get("total_tokens", 0)
            elif metric == "response_time":
                value = log.get("response_time", 0)
            elif metric == "hallucination_score":
                value = log.get("hallucination_score", 0)

            if value is not None:
                time_series.append({
                    "timestamp": log.get("timestamp"),
                    "value": value,
                })

        return time_series

    def clear_logs(self):
        """清空日志（谨慎使用）"""
        if self.log_file.exists():
            self.log_file.unlink()
            print("✅ 日志已清空")
