"""成本与延迟分析模块 - 成本估算、延迟统计、模型对比"""
from typing import Dict, List

import config


class CostEstimator:
    """成本估算器 - 帮 PM 算清楚一个 AI 功能要烧多少钱"""

    def __init__(self):
        self.pricing = config.PRICING

    def estimate_single_call(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict:
        """
        估算单次调用的成本

        Args:
            model: 模型名称
            input_tokens: 输入 token 数
            output_tokens: 输出 token 数

        Returns:
            成本明细字典
        """
        pricing = self.pricing.get(model, {"input": 0.005, "output": 0.01})

        input_cost = input_tokens * pricing["input"] / 1000
        output_cost = output_tokens * pricing["output"] / 1000
        total_cost = input_cost + output_cost

        return {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
        }

    def estimate_monthly(
        self,
        model: str,
        daily_calls: int,
        avg_input_tokens: int,
        avg_output_tokens: int
    ) -> Dict:
        """
        估算月度成本（PM 做预算的核心场景）

        Args:
            model: 模型名称
            daily_calls: 每日调用次数
            avg_input_tokens: 平均输入 token 数
            avg_output_tokens: 平均输出 token 数

        Returns:
            月度成本估算
        """
        single = self.estimate_single_call(model, avg_input_tokens, avg_output_tokens)
        daily_cost = single["total_cost"] * daily_calls
        monthly_cost = daily_cost * 30
        yearly_cost = daily_cost * 365

        return {
            "model": model,
            "daily_calls": daily_calls,
            "cost_per_call": single["total_cost"],
            "daily_cost": daily_cost,
            "monthly_cost": monthly_cost,
            "yearly_cost": yearly_cost,
            "monthly_calls": daily_calls * 30,
            "monthly_tokens": (avg_input_tokens + avg_output_tokens) * daily_calls * 30,
        }

    def compare_models(
        self,
        daily_calls: int,
        avg_input_tokens: int,
        avg_output_tokens: int
    ) -> List[Dict]:
        """
        对比所有模型的月度成本（选型决策的依据）

        Args:
            daily_calls: 每日调用次数
            avg_input_tokens: 平均输入 token
            avg_output_tokens: 平均输出 token

        Returns:
            各模型成本对比列表，按月成本升序排列
        """
        comparison = []
        for model in self.pricing.keys():
            monthly = self.estimate_monthly(
                model, daily_calls, avg_input_tokens, avg_output_tokens
            )
            comparison.append({
                "模型": model,
                "单次成本": monthly["cost_per_call"],
                "日成本": monthly["daily_cost"],
                "月成本": monthly["monthly_cost"],
                "年成本": monthly["yearly_cost"],
            })

        # 按月成本升序排列
        comparison.sort(key=lambda x: x["月成本"])
        return comparison


class LatencyAnalyzer:
    """延迟分析器 - 分析响应时间分布"""

    @staticmethod
    def analyze(response_times: List[float]) -> Dict:
        """
        分析一组响应时间

        Args:
            response_times: 响应时间列表（秒）

        Returns:
            延迟统计：平均、P50、P90、P99、最大、最小
        """
        if not response_times:
            return {
                "count": 0,
                "avg": 0,
                "p50": 0,
                "p90": 0,
                "p99": 0,
                "max": 0,
                "min": 0,
            }

        sorted_times = sorted(response_times)
        n = len(sorted_times)

        def percentile(p: float) -> float:
            """计算百分位数"""
            idx = int(n * p)
            idx = min(idx, n - 1)
            return sorted_times[idx]

        return {
            "count": n,
            "avg": sum(sorted_times) / n,
            "p50": percentile(0.50),  # 中位数：一半请求快于这个值
            "p90": percentile(0.90),  # 90% 的请求快于这个值
            "p99": percentile(0.99),  # 99% 的请求快于这个值（长尾）
            "max": sorted_times[-1],
            "min": sorted_times[0],
        }
