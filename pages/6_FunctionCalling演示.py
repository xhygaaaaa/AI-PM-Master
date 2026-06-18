"""Function Calling 演示 - 让 AI 学会调用工具（Agent 雏形）"""
import streamlit as st

import config
from src import LLMClient
from src.tools import TOOLS_SCHEMA, TOOLS_MAP


def main():
    st.set_page_config(**config.STREAMLIT_PAGE_CONFIG)

    st.title("🛠️ Function Calling 演示")
    st.markdown("""
    **学习目标**：理解 Function Calling（函数调用）—— AI 从"会聊天"到"会干活"的关键

    **核心思想**：
    - 普通问答：AI 只能根据已有知识回答
    - Function Calling：AI 在需要时主动调用工具（计算器、查天气、查知识库），再根据结果回答

    这是 **Agent（智能体）的雏形**。
    """)

    st.divider()

    if not config.LLM_API_KEY:
        st.error("⚠️ 未配置 API Key，请先在 .env 文件中配置")
        st.stop()

    # 展示可用工具
    st.header("🧰 当前可用的工具")
    col1, col2, col3, col4 = st.columns(4)
    tool_intros = {
        "calculator": ("🧮 计算器", "计算数学表达式"),
        "get_current_time": ("🕐 时间", "获取当前时间"),
        "weather_query": ("🌤️ 天气", "查询城市天气（模拟）"),
        "search_knowledge_base": ("📚 知识库", "检索 AI PM 知识库"),
    }
    for col, (name, (title, desc)) in zip([col1, col2, col3, col4], tool_intros.items()):
        with col:
            st.info(f"**{title}**\n\n{desc}")

    st.divider()

    # 提问区
    st.header("💬 试试看")
    st.markdown("""
    **建议问题**（这些问题需要调用工具，能体现 Function Calling 的价值）：
    - `帮我算一下 1234 乘以 5678 等于多少`（调用计算器）
    - `北京今天天气怎么样`（调用天气）
    - `现在几点了`（调用时间）
    - `什么是 Embedding`（调用知识库检索）
    - `深圳天气适合出门吗，顺便帮我算下 88 加 99`（调用多个工具）
    """)

    question = st.text_input(
        "输入你的问题：",
        placeholder="例如：帮我算一下 1234 × 5678",
        key="fc_question"
    )

    if st.button("🚀 发送", type="primary") and question:
        with st.spinner("🤖 AI 思考中（可能会调用工具）..."):
            try:
                client = LLMClient(temperature=0.1)

                system_prompt = """你是一个智能助手，可以调用工具来帮助回答问题。
当遇到计算、查天气、查时间、查专业知识等需求时，主动调用相应的工具。
调用工具后，根据工具返回的结果，用自然语言给用户一个清晰的回答。"""

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ]

                answer, trace = client.chat_with_tools(messages, TOOLS_SCHEMA)

                # 显示最终答案
                st.success("✅ 回答")
                st.info(answer)

                # 显示工具调用轨迹（Agent 的"思考过程"）
                if trace:
                    st.divider()
                    st.subheader("🔍 工具调用轨迹（AI 的思考过程）")
                    st.caption("这就是 Agent 的核心：AI 自己决定调用哪些工具、按什么顺序")

                    for i, step in enumerate(trace, 1):
                        with st.expander(f"步骤 {i}：调用了 `{step['tool']}` 工具", expanded=True):
                            st.markdown(f"**🎯 AI 决定调用**：`{step['tool']}`")
                            st.markdown(f"**📥 传入参数**：")
                            st.json(step["arguments"])
                            st.markdown(f"**📤 工具返回**：")
                            st.code(step["result"], language="text")
                else:
                    st.warning("💡 这次 AI 没有调用任何工具，直接用自己的知识回答了。试试更需要工具的问题。")

            except Exception as e:
                error_str = str(e)
                if "tool" in error_str.lower() or "function" in error_str.lower():
                    st.error(f"""
                    ❌ 调用失败：{e}

                    **可能原因**：你使用的模型不支持 Function Calling。

                    **支持 Function Calling 的模型**：
                    - OpenAI: gpt-3.5-turbo, gpt-4
                    - 通义千问: qwen-turbo, qwen-max
                    - DeepSeek: deepseek-chat
                    - 智谱: glm-4

                    请在 .env 中切换到支持的模型。
                    """)
                else:
                    st.error(f"❌ 出错了：{e}")

    # 原理讲解
    st.divider()
    st.header("📖 Function Calling 原理")

    with st.expander("🔄 完整工作流程（ReAct 循环）", expanded=False):
        st.markdown("""
        ```
        1. 用户提问："北京天气怎么样？"
              ↓
        2. 系统把 [问题 + 工具说明书] 发给 LLM
              ↓
        3. LLM 判断："这需要查天气" → 返回"我要调用 weather_query(city='北京')"
              ↓
        4. 系统执行 weather_query('北京') → 得到"晴，22°C"
              ↓
        5. 系统把工具结果发回给 LLM
              ↓
        6. LLM 根据结果生成回答："北京今天晴，22°C，适合出门"
              ↓
        7. 返回给用户
        ```

        **关键点**：
        - LLM 不直接执行代码，它只是"决定"要调用什么工具
        - 真正执行工具的是你的程序
        - 工具结果再喂回 LLM，让它组织成人话

        这个"思考→行动→观察→再思考"的循环，就是 **ReAct** 模式。
        """)

    with st.expander("🤔 Function Calling vs RAG 有什么区别？"):
        st.markdown("""
        | 维度 | RAG | Function Calling |
        |------|-----|------------------|
        | 解决的问题 | 让 AI 知道私有知识 | 让 AI 能执行动作 |
        | 工作方式 | 先检索文档，塞进 prompt | AI 主动调用函数 |
        | 典型场景 | 知识问答、客服 | 查实时数据、执行操作、计算 |
        | 谁来决定 | 系统固定流程 | AI 自己判断要不要调、调哪个 |

        **可以组合使用**：本演示里的 `search_knowledge_base` 工具，
        就是把 RAG 包装成一个 Function，让 AI 自己决定"要不要查知识库"。
        这就是 RAG + Function Calling 的结合。
        """)

    with st.expander("💼 PM 视角：什么产品该用 Function Calling"):
        st.markdown("""
        **适合的场景**：
        - 需要实时数据：股价、天气、航班、库存
        - 需要执行操作：下单、发邮件、改配置、查数据库
        - 需要精确计算：AI 算数不靠谱，交给计算器工具

        **不适合的场景**：
        - 纯知识问答（用 RAG 更简单）
        - 对延迟敏感（每次工具调用都要多一轮 LLM 交互，更慢）
        - 对成本敏感（多轮交互 = 多次计费）

        **PM 要权衡**：Function Calling 让产品更强大，但更慢、更贵、更难调试。
        要根据场景判断值不值得。
        """)


if __name__ == "__main__":
    main()
