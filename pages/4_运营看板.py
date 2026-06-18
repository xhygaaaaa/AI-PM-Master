"""运营看板 - 数据统计与可视化"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import config
from src import Analytics


def init_session_state():
    """初始化 session state"""
    if 'analytics' not in st.session_state:
        st.session_state.analytics = Analytics()


def main():
    """主函数"""
    st.set_page_config(**config.STREAMLIT_PAGE_CONFIG)
    init_session_state()

    st.title("📈 运营看板")
    st.markdown("""
    **学习目标**：掌握 AI 产品的数据指标体系、数据驱动决策

    在这里，你可以：
    - 查看交互量、成本、采纳率等核心指标
    - 分析问题分类分布
    - 观察幻觉风险趋势
    - 理解 AI 产品经理如何用数据指导产品迭代
    """)

    st.divider()

    # 加载数据
    stats = st.session_state.analytics.get_statistics()
    logs = st.session_state.analytics.load_logs(limit=100)

    if stats['total_interactions'] == 0:
        st.info("""
        📝 暂无数据，请先在主页进行一些提问，系统会自动记录数据。

        数据记录内容包括：
        - 用户问题和 AI 回答
        - 检索结果和幻觉检测
        - Token 消耗和成本
        - 响应时间
        """)
        st.stop()

    # 核心指标
    st.header("📊 核心指标")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "总交互量",
            f"{stats['total_interactions']}",
            help="用户提问的总次数"
        )
        st.metric(
            "总成本",
            f"¥{stats['total_cost']:.4f}",
            help="累计 API 调用成本"
        )

    with col2:
        st.metric(
            "平均响应时间",
            f"{stats['avg_response_time']:.2f}秒",
            help="从提问到返回答案的平均时间"
        )
        st.metric(
            "单次平均成本",
            f"¥{stats['avg_cost_per_interaction']:.4f}",
            help="每次交互的平均成本"
        )

    with col3:
        if stats['feedback_count'] > 0:
            st.metric(
                "采纳率",
                f"{stats['adoption_rate']:.0%}",
                help="用户点「有用」的比例"
            )
            st.caption(f"反馈数：{stats['feedback_count']}")
        else:
            st.metric("采纳率", "暂无数据")
            st.caption("需要用户反馈")

    with col4:
        st.metric(
            "平均 Token 消耗",
            f"{stats['avg_tokens_per_interaction']:.0f}",
            help="每次交互的平均 token 数"
        )

    st.divider()

    # 问题分类分布
    st.header("🏷️ 风险等级分布")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("统计数据")

        risk_data = {
            "风险等级": ["拒答", "低风险", "中风险", "高风险"],
            "数量": [
                stats['refusal_count'],
                stats['low_risk_count'],
                stats['medium_risk_count'],
                stats['high_risk_count']
            ],
            "占比": [
                f"{stats['refusal_rate']:.0%}",
                f"{stats['low_risk_rate']:.0%}",
                f"{stats['medium_risk_rate']:.0%}",
                f"{stats['high_risk_rate']:.0%}",
            ]
        }
        st.dataframe(pd.DataFrame(risk_data), use_container_width=True, hide_index=True)

        st.markdown("""
        **风险等级说明：**
        - **拒答**：超出知识库范围
        - **低风险**：≥70% 关键词有支撑
        - **中风险**：50-70% 关键词有支撑
        - **高风险**：<50% 关键词有支撑
        """)

    with col2:
        st.subheader("可视化")

        # 饼图
        fig = go.Figure(data=[go.Pie(
            labels=risk_data["风险等级"],
            values=risk_data["数量"],
            hole=0.4,
            marker=dict(colors=['#FFA500', '#4CAF50', '#FF9800', '#F44336'])
        )])
        fig.update_layout(
            title="风险等级分布",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # 时间趋势
    st.header("📈 趋势分析")

    if len(logs) > 1:
        # 准备时间序列数据
        df_logs = pd.DataFrame(logs)
        df_logs['timestamp'] = pd.to_datetime(df_logs['timestamp'])
        df_logs = df_logs.sort_values('timestamp')

        # 选择指标
        metric_option = st.selectbox(
            "选择指标",
            ["成本", "Token 消耗", "响应时间", "幻觉得分"],
            key="metric_select"
        )

        # 绘制趋势图
        if metric_option == "成本":
            fig = px.line(
                df_logs,
                x='timestamp',
                y='cost',
                title='成本趋势',
                labels={'cost': '成本（元）', 'timestamp': '时间'}
            )
        elif metric_option == "Token 消耗":
            fig = px.line(
                df_logs,
                x='timestamp',
                y='total_tokens',
                title='Token 消耗趋势',
                labels={'total_tokens': 'Token 数', 'timestamp': '时间'}
            )
        elif metric_option == "响应时间":
            fig = px.line(
                df_logs,
                x='timestamp',
                y='response_time',
                title='响应时间趋势',
                labels={'response_time': '响应时间（秒）', 'timestamp': '时间'}
            )
        else:  # 幻觉得分
            fig = px.line(
                df_logs,
                x='timestamp',
                y='hallucination_score',
                title='防幻觉得分趋势',
                labels={'hallucination_score': '得分', 'timestamp': '时间'}
            )

        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("数据量不足，至少需要 2 条记录才能显示趋势")

    st.divider()

    # 详细日志
    st.header("📋 交互日志")

    if logs:
        # 转换为 DataFrame
        df_logs = pd.DataFrame(logs)

        # 选择显示的列
        display_columns = [
            'timestamp',
            'question',
            'answer',
            'risk_level',
            'hallucination_score',
            'total_tokens',
            'cost',
            'response_time'
        ]

        # 过滤存在的列
        display_columns = [col for col in display_columns if col in df_logs.columns]

        # 格式化
        df_display = df_logs[display_columns].copy()

        if 'timestamp' in df_display.columns:
            df_display['timestamp'] = pd.to_datetime(df_display['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        if 'hallucination_score' in df_display.columns:
            df_display['hallucination_score'] = df_display['hallucination_score'].apply(
                lambda x: f"{x:.0%}" if pd.notna(x) else "N/A"
            )
        if 'cost' in df_display.columns:
            df_display['cost'] = df_display['cost'].apply(lambda x: f"¥{x:.4f}")
        if 'response_time' in df_display.columns:
            df_display['response_time'] = df_display['response_time'].apply(lambda x: f"{x:.2f}秒")

        # 显示
        st.dataframe(df_display, use_container_width=True, height=400)

        # 导出
        csv = df_logs.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 下载日志 CSV",
            data=csv,
            file_name=f"interaction_logs.csv",
            mime="text/csv"
        )

    st.divider()

    # 管理操作
    st.header("⚙️ 数据管理")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("清空日志")
        st.warning("⚠️ 此操作不可恢复")
        if st.button("🗑️ 清空所有日志", type="secondary"):
            st.session_state.analytics.clear_logs()
            st.success("✅ 日志已清空")
            st.rerun()

    with col2:
        st.subheader("刷新数据")
        if st.button("🔄 刷新", type="secondary"):
            st.rerun()

    # 学习提示
    st.divider()
    st.header("💡 AI 产品指标体系")

    with st.expander("📖 核心指标解读"):
        st.markdown("""
        **北极星指标**（最重要的一个）：
        - 通常是"用户问题解决率"或"采纳率"
        - 本项目用"采纳率"（用户点"有用"的比例）

        **一级指标**：
        - **交互量**：使用深度
        - **采纳率**：产品质量
        - **响应时间**：性能体验
        - **成本**：商业可行性

        **二级指标**（AI 特有）：
        - **拒答率**：知识库覆盖度
        - **幻觉率**：可信度
        - **平均 Token 消耗**：成本效率
        - **人工接管率**（本项目未实现）：AI 解决不了转人工的比例
        """)

    with st.expander("📖 如何用数据驱动产品迭代？"):
        st.markdown("""
        **场景 1：拒答率过高（如 >30%）**
        - 原因：知识库覆盖不全
        - 行动：分析拒答的问题，补充知识库文档

        **场景 2：高风险回答比例高（如 >20%）**
        - 原因：Prompt 约束不够、温度太高
        - 行动：优化 Prompt、降低 Temperature

        **场景 3：采纳率低（如 <50%）**
        - 原因：回答质量差、不够准确
        - 行动：分析用户点"没用"的问题，针对性优化

        **场景 4：成本过高**
        - 原因：输出太长、调用次数多
        - 行动：限制 max_tokens、增加缓存、换便宜模型

        **场景 5：响应时间慢（如 >5 秒）**
        - 原因：检索慢、模型慢
        - 行动：优化向量索引、换快速模型、流式输出
        """)

    with st.expander("📖 本项目的数据埋点"):
        st.markdown("""
        **每次交互记录的数据**：
        - 用户问题和 AI 回答
        - 检索到的文档数量和相似度
        - 幻觉检测得分和风险等级
        - 使用的模型和参数（temperature 等）
        - Token 消耗（输入/输出分开）
        - 成本（根据 token 单价计算）
        - 响应时间
        - 用户反馈（有用/没用）

        **存储方式**：
        - JSONL 格式（每行一个 JSON）
        - 文件路径：data/logs/interactions.jsonl
        - 可以用任何支持 JSON 的工具分析

        **在真实产品中**：
        - 还要记录用户 ID、会话 ID
        - 记录追问、放弃、转人工等行为
        - 上报到数据平台（如 Google Analytics、神策）
        """)


if __name__ == "__main__":
    main()
