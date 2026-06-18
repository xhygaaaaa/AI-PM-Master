"""LLM 调用客户端 - 封装大模型 API 调用"""
import time
from typing import List, Tuple, Optional, Dict
from openai import OpenAI

import config


class LLMClient:
    """大模型调用客户端（兼容 OpenAI API 格式）"""

    def __init__(
        self,
        model: str = None,
        temperature: float = None,
        max_tokens: int = None,
        top_p: float = None
    ):
        """
        初始化 LLM 客户端

        Args:
            model: 模型名称，默认使用 config 中的配置
            temperature: 温度参数，默认使用 config 中的配置
            max_tokens: 最大输出 token 数，默认使用 config 中的配置
            top_p: top_p 参数，默认使用 config 中的配置
        """
        # 初始化 OpenAI 客户端（兼容各种 API）
        self.client = OpenAI(
            base_url=config.LLM_BASE_URL,
            api_key=config.LLM_API_KEY
        )

        # 参数配置（允许覆盖）
        self.model = model or config.LLM_MODEL
        self.temperature = temperature if temperature is not None else config.LLM_TEMPERATURE
        self.max_tokens = max_tokens or config.LLM_MAX_TOKENS
        self.top_p = top_p if top_p is not None else config.LLM_TOP_P

        # 统计信息
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0

    def _call_api_with_retry(
        self,
        messages: List[Dict[str, str]],
        max_retries: int = 3
    ) -> Tuple[str, int, int]:
        """
        调用 API 并自动重试（处理 429 限流）

        Args:
            messages: 对话消息列表
            max_retries: 最大重试次数

        Returns:
            (回答内容, 输入 tokens, 输出 tokens)
        """
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    top_p=self.top_p
                )

                # 提取回答和 token 统计
                answer = response.choices[0].message.content
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens

                # 更新统计
                self.total_input_tokens += input_tokens
                self.total_output_tokens += output_tokens
                self.total_calls += 1

                return answer, input_tokens, output_tokens

            except Exception as e:
                error_str = str(e)

                # 检测 429 限流错误
                if "429" in error_str or "rate" in error_str.lower():
                    if attempt < max_retries - 1:
                        # 指数退避（3秒、6秒、9秒）
                        wait_time = (attempt + 1) * 3
                        print(f"⚠️  遇到限流（429），等待 {wait_time} 秒后重试...")
                        time.sleep(wait_time)
                        continue

                # 其他错误或重试次数用尽
                raise e

        raise Exception("API 调用失败，已达最大重试次数")

    def answer_question(
        self,
        question: str,
        retrieved_docs: List[Tuple[str, str, float]],
        system_prompt: str = None,
        user_prompt_template: str = None
    ) -> Tuple[str, int, int]:
        """
        基于检索文档生成答案

        Args:
            question: 用户问题
            retrieved_docs: 检索到的文档 [(文档名称, 内容, 得分), ...]
            system_prompt: 系统提示词，默认使用 config 中的
            user_prompt_template: 用户提示词模板，默认使用 config 中的

        Returns:
            (答案, 输入 tokens, 输出 tokens)
        """
        # 使用默认 prompt
        if system_prompt is None:
            system_prompt = config.DEFAULT_SYSTEM_PROMPT
        if user_prompt_template is None:
            user_prompt_template = config.USER_PROMPT_TEMPLATE

        # 构建上下文（拼接检索到的文档）
        context_parts = []
        for i, (doc_name, content, score) in enumerate(retrieved_docs, 1):
            context_parts.append(f"[文档 {i} - {doc_name}] (相似度: {score:.3f})\n{content}")

        context = "\n\n".join(context_parts)

        # 填充 user prompt 模板
        user_prompt = user_prompt_template.format(
            context=context,
            question=question
        )

        # 构建消息列表
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # 调用 API
        return self._call_api_with_retry(messages)

    def chat(
        self,
        messages: List[Dict[str, str]]
    ) -> Tuple[str, int, int]:
        """
        通用的对话接口（支持多轮对话）

        Args:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}, ...]

        Returns:
            (回答, 输入 tokens, 输出 tokens)
        """
        return self._call_api_with_retry(messages)

    def chat_with_tools(
        self,
        messages: List[Dict],
        tools: List[Dict],
        max_rounds: int = 5
    ) -> Tuple[str, List[Dict]]:
        """
        支持 Function Calling 的对话（Agent 的雏形）

        工作流程（ReAct 思想）：
        1. 把工具说明书 + 用户问题发给 LLM
        2. LLM 决定：直接回答 还是 调用工具
        3. 如果要调用工具，执行工具，把结果再发回给 LLM
        4. 循环，直到 LLM 给出最终答案

        Args:
            messages: 初始消息列表
            tools: 工具 schema（OpenAI Function Calling 格式）
            max_rounds: 最大循环轮数（防止死循环）

        Returns:
            (最终回答, 执行轨迹列表)
            轨迹列表记录每一步：LLM 想调用什么工具、工具返回了什么
        """
        from src.tools import execute_tool
        import json

        trace = []  # 记录执行轨迹，用于在界面上展示 Agent 的"思考过程"

        for round_num in range(max_rounds):
            # 调用 LLM（带工具）
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                tools=tools,
                tool_choice="auto",  # 让 LLM 自己决定是否调用工具
            )

            message = response.choices[0].message

            # 情况 1：LLM 决定调用工具
            if message.tool_calls:
                # 把 LLM 的工具调用请求加入消息历史
                messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in message.tool_calls
                    ],
                })

                # 逐个执行工具
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except Exception:
                        arguments = {}

                    # 执行工具
                    tool_result = execute_tool(tool_name, arguments)

                    # 记录轨迹
                    trace.append({
                        "round": round_num + 1,
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": tool_result,
                    })

                    # 把工具结果发回给 LLM
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    })

                # 继续下一轮，让 LLM 根据工具结果生成回答
                continue

            # 情况 2：LLM 直接给出最终答案
            else:
                return message.content, trace

        # 超过最大轮数
        return "（达到最大调用轮数，未能得出最终答案）", trace

    def get_stats(self) -> Dict:
        """
        获取调用统计信息

        Returns:
            统计字典
        """
        total_cost = config.get_token_cost(
            self.model,
            self.total_input_tokens,
            self.total_output_tokens
        )

        return {
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": total_cost,
            "avg_input_tokens": self.total_input_tokens / max(self.total_calls, 1),
            "avg_output_tokens": self.total_output_tokens / max(self.total_calls, 1),
            "avg_cost_per_call": total_cost / max(self.total_calls, 1),
        }

    def reset_stats(self):
        """重置统计信息"""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0
