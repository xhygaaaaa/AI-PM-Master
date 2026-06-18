"""幻觉检测器 - 检测 AI 回答中可能编造的内容"""
import re
from typing import List, Tuple, Dict, Set


class HallucinationDetector:
    """幻觉检测器（基于关键词匹配的方案 A）"""

    def __init__(self):
        """初始化幻觉检测器"""
        pass

    def extract_keywords(self, text: str) -> Set[str]:
        """
        提取文本中的关键词（改进版，避免垃圾词）

        提取策略：
        1. 提取"数字+单位"组合（如 7天、5ATM、2700K）
        2. 按标点和连接词切分短语
        3. 保留 2-5 字的有意义中文短语
        4. 过滤停用词

        Args:
            text: 输入文本

        Returns:
            关键词集合
        """
        keywords = set()

        # 1. 提取"数字+单位"组合（专业术语）
        number_patterns = [
            r'\d+[天日小时分钟秒]',      # 时间：7天、2小时
            r'\d+ATM',                     # 防水等级：5ATM
            r'\d+米',                       # 距离：5米
            r'\d+[KkMm]',                  # 色温/存储：2700K、100M
            r'\d+%',                        # 百分比：50%
            r'\d+-\d+[KkMm位]',            # 范围：2700-6500K、6-12位
            r'\d+枚',                       # 数量：100枚
            r'\d+\.?\d*秒',                 # 小数秒：0.3秒
            r'\d+[寸英]',                   # 尺寸：5寸、6英寸
            r'\d+mAh',                      # 电池：3000mAh
            r'\d+W',                        # 功率：10W
        ]
        for pattern in number_patterns:
            matches = re.findall(pattern, text)
            keywords.update(matches)

        # 2. 移除标点和连接词
        clean_text = re.sub(r'[，。！？、；：“”‘’（）()《》【】\[\]]', ' ', text)

        # 常见的虚词、连接词
        filler_words = [
            '的', '了', '是', '在', '和', '与', '或', '即可',
            '可以', '需要', '然后', '接着', '约', '大约', '左右',
            '进行', '通过', '使用', '根据', '如果', '因为', '所以',
        ]
        for word in filler_words:
            clean_text = clean_text.replace(word, ' ')

        # 3. 提取 2-5 字的中文短语
        phrases = re.findall(r'[一-龥]{2,5}', clean_text)

        # 4. 过滤停用词
        stopwords = {
            '然后', '接着', '如果', '这个', '那个', '进行', '开始',
            '因此', '所以', '但是', '不过', '而且', '并且', '或者',
            '以及', '就是', '也是', '都是', '只是', '还是', '比如',
            '例如', '其实', '确实', '当然', '不能', '可能', '应该',
        }
        meaningful_phrases = [p for p in phrases if p not in stopwords]
        keywords.update(meaningful_phrases)

        return keywords

    def detect(
        self,
        answer: str,
        retrieved_docs: List[Tuple[str, str, float]]
    ) -> Dict:
        """
        检测 AI 回答中的潜在幻觉

        方案 A：检查回答的关键词有多少能在检索文档中找到支撑

        Args:
            answer: AI 生成的回答
            retrieved_docs: 检索到的文档 [(文档名, 内容, 得分), ...]

        Returns:
            检测结果字典：
            {
                "score": float,              # 防幻觉得分（0-1，越高越好）
                "total_keywords": int,       # 回答的总关键词数
                "supported_keywords": int,   # 有文档支撑的关键词数
                "unsupported_keywords": List[str],  # 无支撑的关键词
                "all_keywords": List[str],   # 所有关键词
                "risk_level": str,           # 风险等级：low/medium/high
            }
        """
        # 1. 提取回答的关键词
        answer_keywords = self.extract_keywords(answer)

        if len(answer_keywords) == 0:
            # 回答太短或没有实质内容
            return {
                "score": 0.0,
                "total_keywords": 0,
                "supported_keywords": 0,
                "unsupported_keywords": [],
                "all_keywords": [],
                "risk_level": "unknown",
            }

        # 2. 合并所有检索文档的内容
        all_doc_content = " ".join([content for _, content, _ in retrieved_docs])
        doc_keywords = self.extract_keywords(all_doc_content)

        # 3. 计算有多少回答关键词能在文档中找到
        supported = answer_keywords & doc_keywords
        unsupported = answer_keywords - doc_keywords

        # 4. 计算防幻觉得分
        score = len(supported) / len(answer_keywords)

        # 5. 判断风险等级
        if score >= 0.7:
            risk_level = "low"       # 低风险：70% 以上有支撑
        elif score >= 0.5:
            risk_level = "medium"    # 中风险：50-70% 有支撑
        else:
            risk_level = "high"      # 高风险：不到 50% 有支撑

        return {
            "score": score,
            "total_keywords": len(answer_keywords),
            "supported_keywords": len(supported),
            "unsupported_keywords": sorted(list(unsupported)),
            "all_keywords": sorted(list(answer_keywords)),
            "risk_level": risk_level,
        }

    def is_refusal(self, answer: str, refusal_signals: List[str] = None) -> bool:
        """
        判断 AI 是否拒答（识别超纲问题）

        Args:
            answer: AI 回答
            refusal_signals: 拒答信号词列表，默认使用 config 中的

        Returns:
            是否拒答
        """
        if refusal_signals is None:
            from config import REFUSAL_SIGNALS
            refusal_signals = REFUSAL_SIGNALS

        return any(signal in answer for signal in refusal_signals)

    def classify_answer(
        self,
        answer: str,
        hallucination_result: Dict
    ) -> Tuple[str, str]:
        """
        对回答进行分类

        分类逻辑：
        1. 先判断是否拒答（超纲问题）
        2. 再判断幻觉风险等级

        Args:
            answer: AI 回答
            hallucination_result: 幻觉检测结果

        Returns:
            (类别, 说明)
            类别：refusal / low_risk / medium_risk / high_risk
        """
        # 1. 判断是否拒答
        if self.is_refusal(answer):
            return "refusal", "AI 拒答，问题超出知识库范围"

        # 2. 根据幻觉风险分类
        risk_level = hallucination_result["risk_level"]

        if risk_level == "low":
            return "low_risk", f"低风险：{hallucination_result['score']:.0%} 的关键词有文档支撑"
        elif risk_level == "medium":
            return "medium_risk", f"中风险：{hallucination_result['score']:.0%} 的关键词有文档支撑，部分内容可能不准确"
        else:  # high
            return "high_risk", f"高风险：仅 {hallucination_result['score']:.0%} 的关键词有文档支撑，可能存在较多编造内容"
