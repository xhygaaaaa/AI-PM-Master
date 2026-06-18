"""FastAPI 评测微服务 - 评测核心逻辑（LLM-as-judge）"""
import re
import sys
from pathlib import Path

# 把项目根目录加入路径，以便复用 config 和 LLMClient
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config
from src.llm_client import LLMClient


# 评判者的 System Prompt（独立于主问答的 prompt）
JUDGE_SYSTEM_PROMPT = """你是一个专业、严格的 AI 答案评判者。

你的任务：评估"AI 回答"相对于"参考上下文"和"用户问题"的质量。

评分维度：
1. 忠实度（最重要）：回答是否只基于参考上下文，没有编造
2. 完整度：是否完整回答了用户问题
3. 清晰度：表达是否清晰、有条理

评分标准（0-10 分）：
- 9-10 分：完美。准确、完整、清晰，完全基于上下文
- 7-8 分：良好。基本准确，有小瑕疵
- 5-6 分：及格。部分正确，有明显不足或少量编造
- 3-4 分：较差。有错误、遗漏，或编造了上下文中没有的内容
- 0-2 分：很差。大量错误或编造，答非所问

输出格式（必须严格遵守）：
评分：X 分
理由：（一句话说明扣分点或亮点）
"""


def parse_score(judge_output: str) -> float:
    """
    从评判输出中解析分数

    Args:
        judge_output: LLM 评判的原始输出

    Returns:
        原始分数（0-10）
    """
    # 优先匹配"评分：X 分"格式
    match = re.search(r'评分[：:]\s*(\d+(?:\.\d+)?)\s*分?', judge_output)
    if match:
        return float(match.group(1))

    # 退而求其次，匹配"X 分"
    match = re.search(r'(\d+(?:\.\d+)?)\s*分', judge_output)
    if match:
        return float(match.group(1))

    # 再退一步，匹配任何 0-10 的独立数字
    match = re.search(r'\b([0-9]|10)\b', judge_output)
    if match:
        return float(match.group(1))

    return 0.0


def judge_single(
    question: str,
    answer: str,
    context: str,
    judge_model: str = None,
    judge_temperature: float = None
) -> dict:
    """
    对单条回答进行 LLM-as-judge 评分

    Args:
        question: 用户问题
        answer: AI 回答
        context: 参考上下文
        judge_model: 评判模型（默认用 config.JUDGE_MODEL）
        judge_temperature: 评判温度（默认用 config.JUDGE_TEMPERATURE）

    Returns:
        {
            "score": float,      # 0-1
            "raw_score": float,  # 0-10
            "reason": str,
            "success": bool,
            "error": str or None,
        }
    """
    if judge_model is None:
        judge_model = config.JUDGE_MODEL
    if judge_temperature is None:
        judge_temperature = config.JUDGE_TEMPERATURE

    judge_user_prompt = f"""参考上下文：
{context}

---

用户问题：
{question}

---

AI 回答：
{answer}

---

请按规定格式评估这个回答的质量。"""

    try:
        client = LLMClient(model=judge_model, temperature=judge_temperature)
        result, _, _ = client.chat([
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": judge_user_prompt},
        ])

        raw_score = parse_score(result)

        return {
            "score": raw_score / 10.0,
            "raw_score": raw_score,
            "reason": result,
            "success": True,
            "error": None,
        }

    except Exception as e:
        return {
            "score": 0.0,
            "raw_score": 0.0,
            "reason": "",
            "success": False,
            "error": str(e),
        }
