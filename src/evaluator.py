"""评测模块 - 离线评测与 LLM-as-judge"""
import csv
from typing import List, Dict, Tuple
from pathlib import Path

import config
from src.llm_client import LLMClient


class Evaluator:
    """评测器"""

    def __init__(self):
        """初始化评测器"""
        pass

    def load_test_set(self, file_path: str) -> List[Dict]:
        """
        加载测试集

        CSV 格式：
        question,expected_answer,category

        Args:
            file_path: CSV 文件路径

        Returns:
            测试题列表 [{"question": ..., "expected_answer": ..., "category": ...}, ...]
        """
        test_cases = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    test_cases.append(row)
            print(f"✅ 加载测试集：{len(test_cases)} 题")
        except Exception as e:
            print(f"❌ 加载测试集失败：{e}")

        return test_cases

    def run_evaluation(
        self,
        test_cases: List[Dict],
        answer_func,  # 回答函数：接收 question，返回 (answer, input_tokens, output_tokens)
        progress_callback=None  # 进度回调函数
    ) -> List[Dict]:
        """
        运行评测

        Args:
            test_cases: 测试题列表
            answer_func: 回答函数
            progress_callback: 进度回调，接收 (current, total, question)

        Returns:
            评测结果列表 [{"question": ..., "answer": ..., "score": ..., ...}, ...]
        """
        results = []
        total = len(test_cases)

        for i, test_case in enumerate(test_cases, 1):
            question = test_case["question"]

            # 调用进度回调
            if progress_callback:
                progress_callback(i, total, question)

            try:
                # 调用回答函数
                answer, input_tokens, output_tokens = answer_func(question)

                # 记录结果
                result = {
                    "question": question,
                    "answer": answer,
                    "expected_answer": test_case.get("expected_answer", ""),
                    "category": test_case.get("category", ""),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cost": config.get_token_cost(
                        config.LLM_MODEL,
                        input_tokens,
                        output_tokens
                    ),
                    "error": None,
                }
            except Exception as e:
                # 记录错误
                result = {
                    "question": question,
                    "answer": "",
                    "expected_answer": test_case.get("expected_answer", ""),
                    "category": test_case.get("category", ""),
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost": 0,
                    "error": str(e),
                }

            results.append(result)

        return results

    def llm_as_judge(
        self,
        question: str,
        answer: str,
        context: str,
        judge_model: str = None,
        judge_temperature: float = None
    ) -> Tuple[float, str]:
        """
        使用 LLM 作为评判者，对答案打分

        评判标准：
        1. 答案是否与提供的上下文一致（没有编造）
        2. 答案是否完整回答了问题
        3. 答案是否清晰易懂

        Args:
            question: 用户问题
            answer: AI 回答
            context: 参考上下文（检索到的文档）
            judge_model: 评判使用的模型
            judge_temperature: 评判的温度

        Returns:
            (得分 0-10, 评判理由)
        """
        if judge_model is None:
            judge_model = config.JUDGE_MODEL
        if judge_temperature is None:
            judge_temperature = config.JUDGE_TEMPERATURE

        # 构建评判 prompt
        judge_system_prompt = """你是一个专业的 AI 答案评判者。

你的任务：
1. 评估 AI 的回答是否准确、完整、清晰
2. 给出 0-10 分的评分
3. 说明评分理由

评分标准：
- 9-10 分：完美回答，准确、完整、清晰
- 7-8 分：良好，基本准确，有小瑕疵
- 5-6 分：及格，部分正确，有明显不足
- 3-4 分：较差，有错误或遗漏重要信息
- 0-2 分：很差，完全错误或编造内容

输出格式：
评分：X 分
理由：...
"""

        judge_user_prompt = f"""参考上下文：
{context}

---

用户问题：
{question}

---

AI 回答：
{answer}

---

请评估这个回答的质量。
"""

        # 调用 LLM
        client = LLMClient(
            model=judge_model,
            temperature=judge_temperature
        )

        try:
            result, _, _ = client.chat([
                {"role": "system", "content": judge_system_prompt},
                {"role": "user", "content": judge_user_prompt}
            ])

            # 解析评分
            score = self._parse_score(result)
            return score, result

        except Exception as e:
            print(f"⚠️  LLM-as-judge 调用失败：{e}")
            return 0.0, f"评判失败：{e}"

    def _parse_score(self, judge_output: str) -> float:
        """
        从评判输出中解析分数

        Args:
            judge_output: LLM 评判的输出

        Returns:
            分数（0-10，转换为 0-1）
        """
        import re

        # 尝试提取"评分：X 分"格式
        match = re.search(r'评分[：:]\s*(\d+(?:\.\d+)?)\s*分', judge_output)
        if match:
            score = float(match.group(1))
            return score / 10.0  # 转换为 0-1

        # 尝试提取纯数字
        match = re.search(r'(\d+(?:\.\d+)?)\s*分', judge_output)
        if match:
            score = float(match.group(1))
            return score / 10.0

        # 默认返回 0
        return 0.0

    def calculate_metrics(self, results: List[Dict]) -> Dict:
        """
        计算评测指标

        Args:
            results: 评测结果列表

        Returns:
            指标字典
        """
        total = len(results)
        if total == 0:
            return {}

        # 成功的测试（无错误）
        successful = [r for r in results if not r.get("error")]
        success_count = len(successful)

        # 总成本
        total_cost = sum(r.get("cost", 0) for r in results)

        # 总 tokens
        total_tokens = sum(r.get("input_tokens", 0) + r.get("output_tokens", 0) for r in results)

        # 如果有 score 字段（LLM-as-judge），计算平均分
        scored_results = [r for r in results if "score" in r and r["score"] is not None]
        avg_score = sum(r["score"] for r in scored_results) / len(scored_results) if scored_results else None

        return {
            "total_cases": total,
            "success_count": success_count,
            "error_count": total - success_count,
            "success_rate": success_count / total,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "avg_cost_per_case": total_cost / total,
            "avg_tokens_per_case": total_tokens / total,
            "avg_score": avg_score,
        }
