"""参数调优实验室 - 实时调节参数，观察效果"""
import streamlit as st
import time

import config
from src import LLMClient, HallucinationDetector


def init_session_state():
    """初始化 session state"""
    if 'rag' not in st.session_state:
        from src import load_knowledge_base
        st.session_state.rag = load_knowledge_base()
    if 'hallucination_detector' not in st.session_state:
        st.session_state.hallucination_detector = HallucinationDetector()
    if 'experiment_results' not in st.session_state:
        st.session_state.experiment_results = []


def main():
    """主函数"""
    st.set_page_config(**config.STREAMLIT_PAGE_CONFIG)
    init_session_state()

    st.title("🎛️ 参数调优实验室")
    st.markdown("""
    **学习目标**：理解 Temperature、Top-p、Max tokens 等参数如何影响 AI 的输出

    在这里，你可以：
    - 实时调节参数，观察同一个问题的不同回答
    - 对比不同参数组合的效果
    - 理解什么场景该用什么参数
    """)

    st.divider()

    # 检查知识库
    if not st.session_state.rag or not st.session_state.rag.documents:
        st.warning("⚠️ 知识库为空，请先在主页加载知识库")
        st.stop()

    # 参数配置区
    st.header("⚙️ 参数配置")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("实验组 A")
        temp_a = st.slider(
            "Temperature（温度）",
            min_value=0.0,
            max_value=2.0,
            value=0.1,
            step=0.1,
            key="temp_a",
            help="控制随机性。0=确定，2=很随机"
        )
        top_p_a = st.slider(
            "Top-p（核采样）",
            min_value=0.0,
            max_value=1.0,
            value=0.9,
            step=0.05,
            key="top_p_a",
            help="只在累计概率前 p 的词里选"
        )
        max_tokens_a = st.slider(
            "Max Tokens（最大输出长度）",
            min_value=100,
            max_value=2000,
            value=500,
            step=100,
            key="max_tokens_a",
            help="限制回答最多生成多少 token"
        )

    with col2:
        st.subheader("实验组 B")
        temp_b = st.slider(
            "Temperature（温度）",
            min_value=0.0,
            max_value=2.0,
            value=0.9,
            step=0.1,
            key="temp_b"
        )
        top_p_b = st.slider(
            "Top-p（核采样）",
            min_value=0.0,
            max_value=1.0,
            value=0.95,
            step=0.05,
            key="top_p_b"
        )
        max_tokens_b = st.slider(
            "Max Tokens（最大输出长度）",
            min_value=100,
            max_value=2000,
            value=500,
            step=100,
            key="max_tokens_b"
        )

    st.divider()

    # 输入问题
    st.header("💬 提问")
    question = st.text_input(
        "输入问题，系统会用两组参数分别回答：",
        placeholder="例如：什么是 Temperature 参数？",
        key="experiment_question"
    )

    run_experiment = st.button("🚀 运行实验", type="primary", use_container_width=True)

    # 运行实验
    if run_experiment and question:
        st.divider()
        st.header("📊 实验结果")

        # 检索文档（两组共用）
        with st.spinner("🔍 检索知识库..."):
            retrieved_docs = st.session_state.rag.retrieve(question, top_k=config.TOP_K)

            if not retrieved_docs:
                st.warning("❌ 未找到相关内容")
                st.stop()

        # 实验组 A
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🅰️ 实验组 A")
            st.caption(f"Temperature={temp_a}, Top-p={top_p_a}, Max tokens={max_tokens_a}")

            with st.spinner("AI 生成中..."):
                start_time = time.time()

                client_a = LLMClient(
                    temperature=temp_a,
                    top_p=top_p_a,
                    max_tokens=max_tokens_a
                )
                answer_a, input_tokens_a, output_tokens_a = client_a.answer_question(
                    question,
                    retrieved_docs
                )

                response_time_a = time.time() - start_time

            # 幻觉检测
            hallucination_a = st.session_state.hallucination_detector.detect(
                answer_a,
                retrieved_docs
            )

            # 显示结果
            st.info(answer_a)

            # 指标
            st.metric("响应时间", f"{response_time_a:.2f}秒")
            st.metric("防幻觉得分", f"{hallucination_a['score']:.0%}")
            st.metric("输出 tokens", output_tokens_a)

        with col2:
            st.subheader("🅱️ 实验组 B")
            st.caption(f"Temperature={temp_b}, Top-p={top_p_b}, Max tokens={max_tokens_b}")

            with st.spinner("AI 生成中..."):
                start_time = time.time()

                client_b = LLMClient(
                    temperature=temp_b,
                    top_p=top_p_b,
                    max_tokens=max_tokens_b
                )
                answer_b, input_tokens_b, output_tokens_b = client_b.answer_question(
                    question,
                    retrieved_docs
                )

                response_time_b = time.time() - start_time

            # 幻觉检测
            hallucination_b = st.session_state.hallucination_detector.detect(
                answer_b,
                retrieved_docs
            )

            # 显示结果
            st.info(answer_b)

            # 指标
            st.metric("响应时间", f"{response_time_b:.2f}秒")
            st.metric("防幻觉得分", f"{hallucination_b['score']:.0%}")
            st.metric("输出 tokens", output_tokens_b)

        # 对比分析
        st.divider()
        st.subheader("📈 对比分析")

        col1, col2, col3 = st.columns(3)
        with col1:
            diff = hallucination_a['score'] - hallucination_b['score']
            st.metric(
                "防幻觉得分差异",
                f"{abs(diff):.0%}",
                delta=f"{'A 更好' if diff > 0 else 'B 更好' if diff < 0 else '相同'}"
            )
        with col2:
            diff_tokens = output_tokens_a - output_tokens_b
            st.metric(
                "输出长度差异",
                abs(diff_tokens),
                delta=f"{'A 更长' if diff_tokens > 0 else 'B 更长' if diff_tokens < 0 else '相同'}"
            )
        with col3:
            diff_time = response_time_a - response_time_b
            st.metric(
                "速度差异",
                f"{abs(diff_time):.2f}秒",
                delta=f"{'A 更慢' if diff_time > 0 else 'B 更慢' if diff_time < 0 else '相同'}"
            )

        # 结论
        st.markdown("### 💡 实验结论")
        if temp_a < temp_b:
            st.write("- **Temperature 对比**：A 组温度更低，回答更确定、更一致；B 组温度更高，回答更发散、更有变化")
        elif temp_a > temp_b:
            st.write("- **Temperature 对比**：A 组温度更高，回答更发散；B 组温度更低，回答更确定")

        if hallucination_a['score'] > hallucination_b['score']:
            st.write("- **防幻觉效果**：A 组更好，更多关键词有文档支撑")
        elif hallucination_a['score'] < hallucination_b['score']:
            st.write("- **防幻觉效果**：B 组更好，更多关键词有文档支撑")

        if output_tokens_a > output_tokens_b:
            st.write("- **输出长度**：A 组更详细，但成本更高")
        elif output_tokens_a < output_tokens_b:
            st.write("- **输出长度**：B 组更详细，但成本更高")

    # 参数说明
    st.divider()
    st.header("📖 参数说明")

    with st.expander("🌡️ Temperature（温度）"):
        st.markdown("""
        **作用**：控制输出的随机性 / 创造性

        **取值范围**：0 ～ 2（常用 0 ～ 1）

        **效果**：
        - `0`：几乎确定，同样问题每次答得几乎一样
        - `0.3`：略有变化，但仍然保守（你第一个项目就是这个）
        - `0.7～1.0`：发散、有创意，但容易跑偏
        - `>1.0`：很随机，可能胡言乱语

        **应用场景**：
        - 客服机器人：0.1～0.3（要稳定）
        - 营销文案：0.7～0.9（要创意）
        - 代码生成：0.2（要精确）
        """)

    with st.expander("🎯 Top-p（核采样）"):
        st.markdown("""
        **作用**：另一种控制随机性的方式

        **原理**：只在"累计概率前 p"的候选词里挑

        **例子**：`top_p = 0.9` 表示只考虑累计概率达到 90% 的词

        **与 temperature 的关系**：一般只调一个，不要俩一起猛调

        **推荐设置**：
        - 确定性任务：top_p = 0.9，temperature = 0.1
        - 创造性任务：top_p = 0.95，temperature = 0.8
        """)

    with st.expander("📏 Max Tokens（最大输出长度）"):
        st.markdown("""
        **作用**：限制回答最多生成多少 token

        **影响**：
        - 设太小：答案被截断
        - 设太大：费钱、浪费

        **产品决策**：根据实际需求设置合理上限

        **注意**：1 个中文字约 1～2 个 token
        """)


if __name__ == "__main__":
    main()
