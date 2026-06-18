"""全局配置文件 - 集中管理所有配置项"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
load_dotenv()

# ===== 项目路径 =====
# 项目根目录
PROJECT_ROOT = Path(__file__).parent.absolute()

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
PROMPTS_DIR = DATA_DIR / "prompts"
TEST_SETS_DIR = DATA_DIR / "test_sets"
LOG_DIR = DATA_DIR / "logs"

# 确保目录存在
for directory in [DATA_DIR, KNOWLEDGE_BASE_DIR, PROMPTS_DIR, TEST_SETS_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ===== LLM API 配置 =====
# API 基础 URL（兼容 OpenAI 格式的任何服务）
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.minimax.chat/v1")

# API 密钥
LLM_API_KEY = os.getenv("LLM_API_KEY", "")

# 模型名称
LLM_MODEL = os.getenv("LLM_MODEL", "abab6.5-chat")

# 温度参数（控制随机性，0=确定，1=随机）
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))

# 最大输出 token 数
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1000"))

# Top-p 核采样
LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.9"))

# ===== RAG 配置 =====
# 检索返回的文档数量
TOP_K = int(os.getenv("TOP_K", "3"))

# Embedding 模型名称（sentence-transformers）
# 推荐中文模型：
# - paraphrase-multilingual-MiniLM-L12-v2 (小巧，118MB)
# - sentence-transformers/distiluse-base-multilingual-cased-v2 (通用)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

# 向量维度（根据 Embedding 模型自动确定，这里仅作说明）
# paraphrase-multilingual-MiniLM-L12-v2: 384 维

# ===== 评测服务配置 =====
# FastAPI 评测服务端口
EVALUATION_SERVICE_PORT = int(os.getenv("EVALUATION_SERVICE_PORT", "8001"))

# LLM-as-judge 使用的模型
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "abab6.5-chat")

# Judge 的温度（通常设低，要求客观评分）
JUDGE_TEMPERATURE = float(os.getenv("JUDGE_TEMPERATURE", "0.1"))

# ===== Prompt 模板 =====
# 默认的 System Prompt（版本 1）
DEFAULT_SYSTEM_PROMPT = """你是一个专业的智能问答助手。

你的职责：
1. 根据提供的参考文档回答用户问题
2. 如果文档中没有相关信息，明确告知"文档中未找到相关信息"
3. 回答要准确、简洁、有条理
4. 引用文档时要指明来源

你不能：
1. 编造文档中不存在的信息
2. 回答超出文档范围的问题（如价格、购买、个人意见）
3. 提供医疗、法律等专业建议
"""

# User Prompt 模板
USER_PROMPT_TEMPLATE = """参考文档：
{context}

---

用户问题：{question}

请根据参考文档回答用户问题。如果文档中没有相关信息，请明确说明。
"""

# ===== 拒答信号词 =====
# 用于识别 AI 是否拒答（超纲问题检测）
REFUSAL_SIGNALS = [
    "文档中未找到",
    "没有相关信息",
    "不在文档中",
    "无法回答",
    "无法提供",
    "不能回答",
    "超出范围",
    "建议咨询",
    "无法作答",
]

# ===== 评测配置 =====
# 默认测试集文件名
DEFAULT_TEST_SET = "standard_test.csv"

# 准确率阈值（用于可视化标记）
ACCURACY_EXCELLENT = 0.8  # 优秀：>= 80%
ACCURACY_GOOD = 0.6       # 良好：>= 60%
# 其余为待改进

# ===== 成本配置（用于成本估算）=====
# 各模型的 Token 单价（元 / 1K tokens）
# 这里是示例价格，实际以官网为准
PRICING = {
    "abab6.5-chat": {
        "input": 0.015,   # 输入 0.015 元 / 1K tokens
        "output": 0.015,  # 输出 0.015 元 / 1K tokens
    },
    "qwen-turbo": {
        "input": 0.002,
        "output": 0.006,
    },
    "deepseek-chat": {
        "input": 0.001,
        "output": 0.002,
    },
    "gpt-3.5-turbo": {
        "input": 0.0015,  # $0.0015 / 1K tokens ≈ 0.011 元（按 7.2 汇率）
        "output": 0.002,
    },
    "gpt-4": {
        "input": 0.03,
        "output": 0.06,
    },
}

def get_token_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    计算单次调用的成本（元）

    Args:
        model: 模型名称
        input_tokens: 输入 token 数
        output_tokens: 输出 token 数

    Returns:
        成本（元）
    """
    if model not in PRICING:
        # 未知模型，使用平均价格估算
        return (input_tokens * 0.005 + output_tokens * 0.01) / 1000

    pricing = PRICING[model]
    cost = (input_tokens * pricing["input"] + output_tokens * pricing["output"]) / 1000
    return cost

# ===== 应用配置 =====
# 是否启用调试模式
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Streamlit 页面配置
STREAMLIT_PAGE_CONFIG = {
    "page_title": "AI 产品经理学习平台",
    "page_icon": "🤖",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}

# ===== 验证配置 =====
if not LLM_API_KEY:
    print("⚠️  警告：未配置 LLM_API_KEY，请复制 .env.example 为 .env 并填入你的 API 密钥")
