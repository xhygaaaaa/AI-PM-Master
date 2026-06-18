"""成本与延迟仪表盘 - PM 的算账工具"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config
from src import Analytics
from src.cost_analyzer import CostEstimator, LatencyAnalyzer


def init_session_state():
    if 'analytics' not in st.session_state:
        st.session_state.analytics = Analytics()
    if 'cost_estimator' not in st.session_state:
        st.session_state.cost_estimator = CostEstimator()


def main():
    st.set_page_config(**config.STREAMLIT_PAGE_CONFIG)
    init_session_state()

    st.title("💰 成本与延迟仪表盘")
    st.markdown("""
    **学习目标**：掌握 AI PM 最值钱的硬技能 —— 算账

    在这里，你可以：
    - 估算一个 AI 功能的月度 / 年度成本
    - 对比不同模型的成本差异（选型决策）
    - 分析响应延迟的分布（P50/P90/P99）
    """)

    st.divider()

    tab1, tab2, tab3 = st.tabs(["📊 成本估算器", "⚖️ 模型成本对比", "⏱️ 延迟分析"])

    # ===== Tab 1: 成本估算器 =====
    with tab1:
        st.header("成本估算器")
        st.markdown("输入业务量，估算 AI 功能要烧多少钱。这是 PM 立项时必做的事。")

        col1, col2 = st.columns(2)
        with col1:
            model = st.selectbox(
                "选择模型",
                list(config.PRICING.keys()),
                key="cost_model"
            )
            daily_calls = st.number_input(
                "每日调用次数",
                min_value=1,
                max_value=10_000_000,
                value=1000,
                step=100,
                help="预估每天有多少次 AI 调用"
            )
        with col2:
            avg_input = st.number_input(
                "平均输入 Token 数",
                min_value=1,
                max_value=100_000,
                value=800,
                step=50,
                help="每次请求的 prompt 长度（含检索文档）"
            )
            avg_output = st.number_input(
                "平均输出 Token 数",
                min_value=1,
                max_value=10_000,
                value=300,
                step=50,
                help="每次回答的长度"
            )

        if st.button("💰 计算成本", type="primary"):
            result = st.session_state.cost_estimator.estimate_monthly(
                model, daily_calls, avg_input, avg_output
            )

            st.divider()
            st.subheader("📋 成本估算结果")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("单次成本", f"¥{result['cost_per_call']:.5f}")
            with col2:
                st.metric("日成本", f"¥{result['daily_cost']:.2f}")
            with col3:
                st.metric("月成本", f"¥{result['monthly_cost']:.2f}")
            with col4:
                st.metric("年成本", f"¥{result['yearly_cost']:.2f}")

            st.info(f"""
            **业务量预估**：
            - 月调用量：{result['monthly_calls']:,} 次
            - 月 Token 消耗：{result['monthly_tokens']:,} tokens

            **PM 视角解读**：
            - 如果这是一个免费功能，月成本 ¥{result['monthly_cost']:.0f} 就是纯支出，要算进运营预算
            - 如果向用户收费，单次成本 ¥{result['cost_per_call']:.5f} 是你的成本底线，定价要高于它
            """)

    # ===== Tab 2: 模型成本对比 =====
    with tab2:
        st.header("模型成本对比")
        st.markdown("同样的业务量，不同模型的成本可能差 10 倍。这是选型决策的核心依据。")

        col1, col2, col3 = st.columns(3)
        with col1:
            cmp_calls = st.number_input("每日调用次数", value=1000, step=100, key="cmp_calls")
        with col2:
            cmp_input = st.number_input("平均输入 Token", value=800, step=50, key="cmp_input")
        with col3:
            cmp_output = st.number_input("平均输出 Token", value=300, step=50, key="cmp_output")

        if st.button("⚖️ 对比所有模型", type="primary"):
            comparison = st.session_state.cost_estimator.compare_models(
                cmp_calls, cmp_input, cmp_output
            )
            df = pd.DataFrame(comparison)

            st.divider()
            st.subheader("📊 成本对比表（按月成本升序）")

            # 格式化显示
            df_display = df.copy()
            df_display["单次成本"] = df_display["单次成本"].apply(lambda x: f"¥{x:.5f}")
            df_display["日成本"] = df_display["日成本"].apply(lambda x: f"¥{x:.2f}")
            df_display["月成本"] = df_display["月成本"].apply(lambda x: f"¥{x:.2f}")
            df_display["年成本"] = df_display["年成本"].apply(lambda x: f"¥{x:.2f}")
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # 柱状图
            fig = px.bar(
                df,
                x="模型",
                y="月成本",
                title="各模型月成本对比",
                labels={"月成本": "月成本（元）"},
                color="月成本",
                color_continuous_scale="RdYlGn_r",
            )
            st.plotly_chart(fig, use_container_width=True)

            # 决策建议
            cheapest = df.iloc[0]
            most_expensive = df.iloc[-1]
            ratio = most_expensive["月成本"] / cheapest["月成本"] if cheapest["月成本"] > 0 else 0

            st.success(f"""
            **💡 选型建议**：
            - 最便宜：**{cheapest['模型']}**（月成本 ¥{cheapest['月成本']:.2f}）
            - 最贵：**{most_expensive['模型']}**（月成本 ¥{most_expensive['月成本']:.2f}）
            - 成本差距：**{ratio:.1f} 倍**

            **PM 决策逻辑**：贵的模型不一定值得。要结合效果（准确率）一起看：
            如果便宜模型准确率够用，就没必要为贵模型多付 {ratio:.0f} 倍的钱。
            这就是"用评测中心测效果 + 用这里算成本"的组合拳。
            """)

    # ===== Tab 3: 延迟分析 =====
    with tab3:
        st.header("延迟分析")
        st.markdown("延迟影响体验。P99 延迟（最慢的 1%）往往是用户流失的元凶。")

        # 从真实日志读取延迟数据
        logs = st.session_state.analytics.load_logs()
        response_times = [
            log["response_time"] for log in logs
            if log.get("response_time") is not None
        ]

        if not response_times:
            st.info("""
            📝 暂无延迟数据。请先在"智能问答"页面提几个问题，系统会记录每次的响应时间。

            **延迟指标科普**：
            - **P50（中位数）**：一半的请求比这快
            - **P90**：90% 的请求比这快
            - **P99**：99% 的请求比这快（剩下 1% 是最慢的长尾）

            为什么看 P99 而不只看平均值？因为平均值会被掩盖。
            假设 100 个请求里 99 个是 1 秒，1 个是 30 秒，
            平均值才 1.3 秒看着挺好，但那 1 个 30 秒的用户已经走了。
            """)
        else:
            stats = LatencyAnalyzer.analyze(response_times)

            st.subheader("📊 延迟统计")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("样本数", stats["count"])
                st.metric("平均延迟", f"{stats['avg']:.2f}秒")
            with col2:
                st.metric("P50（中位数）", f"{stats['p50']:.2f}秒")
                st.metric("P90", f"{stats['p90']:.2f}秒")
            with col3:
                st.metric("P99", f"{stats['p99']:.2f}秒")
                st.metric("最大延迟", f"{stats['max']:.2f}秒")

            # 延迟分布直方图
            fig = px.histogram(
                x=response_times,
                nbins=20,
                title="响应时间分布",
                labels={"x": "响应时间（秒）", "y": "请求数"},
            )
            # 标记 P90、P99
            fig.add_vline(x=stats["p90"], line_dash="dash", line_color="orange",
                          annotation_text="P90")
            fig.add_vline(x=stats["p99"], line_dash="dash", line_color="red",
                          annotation_text="P99")
            st.plotly_chart(fig, use_container_width=True)

            # 体验评估
            p99 = stats["p99"]
            if p99 <= 3:
                st.success(f"✅ P99 延迟 {p99:.2f}秒，体验良好（用户基本无感知等待）")
            elif p99 <= 5:
                st.warning(f"⚠️ P99 延迟 {p99:.2f}秒，可接受但有优化空间")
            else:
                st.error(f"❌ P99 延迟 {p99:.2f}秒，偏慢。建议：流式输出、换更快的模型、加缓存")

    # 学习提示
    st.divider()
    with st.expander("📖 AI PM 如何做成本控制"):
        st.markdown("""
        **成本优化的五个杠杆**：
        1. **换模型**：不是所有任务都要用最强的模型。简单问答用便宜模型就够
        2. **控制输出长度**：max_tokens 设合理值，输出 token 比输入贵 2-5 倍
        3. **压缩 Prompt**：去掉冗余的 system prompt、减少检索文档数（top_k）
        4. **加缓存**：高频相同问题，缓存答案，命中就 0 成本
        5. **限流降级**：高峰期把部分流量导向便宜模型

        **真实案例思路**：
        - 假设一个客服机器人日调用 10 万次
        - 用 GPT-4：月成本可能上万元
        - 换成 DeepSeek + 缓存命中 30%：月成本可能降到几百元
        - 效果差异要用评测中心验证，确认便宜方案准确率够用
        """)


if __name__ == "__main__":
    main()
