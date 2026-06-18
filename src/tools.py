"""工具集 - Function Calling 演示用的本地工具

这些是给 LLM 调用的"工具"。Function Calling 的核心思想：
让 LLM 在需要时主动调用这些函数，从"会聊天"变成"会干活"。

为了让演示无需联网、无需额外密钥，这里的工具都是本地模拟实现。
"""
import re
import math
from datetime import datetime, timedelta


def calculator(expression: str) -> str:
    """
    计算器工具：计算数学表达式

    Args:
        expression: 数学表达式字符串，如 "2 + 3 * 4"

    Returns:
        计算结果字符串
    """
    # 安全检查：只允许数字、运算符、括号、常见数学函数
    allowed = set("0123456789+-*/(). ")
    safe_expr = expression.replace("sqrt", "").replace("pow", "")
    if not all(c in allowed for c in safe_expr if c not in "sqrtpow"):
        # 退一步用正则校验
        if not re.match(r'^[\d\s+\-*/().sqrtpow,]+$', expression):
            return f"错误：表达式包含不允许的字符"

    try:
        # 提供有限的安全函数
        safe_dict = {
            "sqrt": math.sqrt,
            "pow": pow,
            "abs": abs,
            "round": round,
        }
        result = eval(expression, {"__builtins__": {}}, safe_dict)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误：{e}"


def get_current_time(timezone: str = "Asia/Shanghai") -> str:
    """
    时间工具：获取当前时间（模拟，返回固定演示值）

    注意：本环境禁用了实时时钟，这里返回演示用的固定时间。
    在真实项目中，这里会返回 datetime.now()。

    Args:
        timezone: 时区

    Returns:
        当前时间字符串
    """
    # 演示固定值（真实项目用 datetime.now()）
    return f"当前时间（{timezone}）：2026-06-17 21:30:00（演示值）"


def weather_query(city: str) -> str:
    """
    天气查询工具（模拟数据）

    真实项目中这里会调用天气 API（如和风天气、OpenWeather）。
    为了演示无需密钥，这里返回模拟数据。

    Args:
        city: 城市名称

    Returns:
        天气信息字符串
    """
    # 模拟天气数据
    mock_weather = {
        "北京": "晴，22°C，东北风 3 级，空气质量良",
        "上海": "多云，25°C，东南风 2 级，空气质量优",
        "广州": "阵雨，28°C，南风 2 级，湿度 80%",
        "深圳": "雷阵雨，29°C，南风 3 级，注意带伞",
        "杭州": "晴转多云，24°C，微风，空气质量优",
    }
    weather = mock_weather.get(city, f"暂无 {city} 的天气数据（演示仅支持北上广深杭）")
    return f"{city}天气：{weather}"


def search_knowledge_base(query: str) -> str:
    """
    知识库检索工具：从本项目的向量知识库检索

    这个工具把 RAG 检索包装成一个 Function，让 LLM 可以主动决定
    "这个问题我需要查知识库" —— 这是 Agent 的雏形。

    Args:
        query: 检索关键词

    Returns:
        检索到的内容
    """
    try:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src import load_knowledge_base

        rag = load_knowledge_base()
        results = rag.retrieve(query, top_k=2)
        if not results:
            return f"知识库中未找到与「{query}」相关的内容"

        parts = []
        for doc_name, content, score in results:
            parts.append(f"[{doc_name}] {content[:200]}")
        return "\n".join(parts)
    except Exception as e:
        return f"检索失败：{e}"


# ===== 工具定义（OpenAI Function Calling 格式）=====
# 这是给 LLM 看的"工具说明书"，告诉它每个工具能干什么、需要什么参数

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式，支持加减乘除、括号、sqrt（开方）、pow（幂）",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "数学表达式，例如 '2 + 3 * 4' 或 'sqrt(16)'",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取当前的日期和时间",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "时区，默认 Asia/Shanghai",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "weather_query",
            "description": "查询指定城市的天气情况",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'上海'",
                    }
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "从 AI 产品经理知识库中检索相关内容，适合回答专业概念问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "检索关键词，如'什么是Embedding'",
                    }
                },
                "required": ["query"],
            },
        },
    },
]


# 工具名称 → 实际函数的映射表
TOOLS_MAP = {
    "calculator": calculator,
    "get_current_time": get_current_time,
    "weather_query": weather_query,
    "search_knowledge_base": search_knowledge_base,
}


def execute_tool(tool_name: str, arguments: dict) -> str:
    """
    执行指定的工具

    Args:
        tool_name: 工具名称
        arguments: 参数字典

    Returns:
        工具执行结果
    """
    if tool_name not in TOOLS_MAP:
        return f"错误：未知工具 {tool_name}"

    func = TOOLS_MAP[tool_name]
    try:
        return func(**arguments)
    except Exception as e:
        return f"工具执行错误：{e}"
