"""评测中心 - 批量评测与 LLM-as-judge"""
import streamlit as st
import pandas as pd
import time

import config
from src import Evaluator, LLMClient, HallucinationDetector
from src.judge_client import JudgeClient


def init_session_state():
    """初始化 session state"""
    if 'rag' not in st.session_state:
        from src import load_knowledge_base
        st.session_state.rag = load_knowledge_base()
    if 'evaluator' not in st.session_state:
        st.session_state.evaluator = Evaluator()
    if 'hallucination_detector' not in st.session_state:
        st.session_state.hallucination_detector = HallucinationDetector()
    if 'judge_client' not in st.session_state:
        st.session_state.judge_client = JudgeClient()
    if 'evaluation_results' not in st.session_state:
        st.session_state.evaluation_results = None


def main():
    """主函数"""
    st.set_page_config(**config.STREAMLIT_PAGE_CONFIG)
    init_session_state()

    st.title("📊 评测中心")
    st.markdown("""
    **学习目标**：掌握 AI 产品的评测方法 - 离线评测、LLM-as-judge、指标体系

    在这里，你可以：
    - 上传测试集，批量运行评测
    - 使用 LLM-as-judge 自动打分
    - 查看准确率、成本等指标
    - 导出评测报告
    """)

    st.divider()

    # 检查知识库
    if not st.session_state.rag or not st.session_state.rag.documents:
        st.warning("⚠️ 知识库为空，请先在主页加载知识库")
        st.stop()

    # 功能选择
    tab1, tab2 = st.tabs(["📝 批量评测", "📈 评测报告"])

    # Tab 1: 批量评测
    with tab1:
        st.header("批量评测")

        # 上传测试集
        st.subheader("1️⃣ 准备测试集")

        st.markdown("""
        **CSV 格式要求：**
        - 必须包含 `question` 列（问题）
        - 可选 `expected_answer` 列（期望答案，用于人工对比）
        - 可选 `category` 列（问题分类）

        **示例：**
        ```csv
        question,expected_answer,category
        什么是 Temperature 参数？,控制随机性的参数,基础概念
        如何调节温度参数？,通过 API 参数设置,操作指南
        ```
        """)

        uploaded_file = st.file_uploader(
            "上传测试集 CSV 文件",
            type=["csv"],
            help="如果没有测试集，可以先跳过，直接用示例问题测试"
        )

        # 或者使用示例测试集
        use_demo = st.checkbox("使用示例测试集（3 个问题）", value=False)

        test_cases = []

        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file)
                if 'question' not in df.columns:
                    st.error("❌ CSV 文件必须包含 'question' 列")
                else:
                    test_cases = df.to_dict('records')
                    st.success(f"✅ 已加载 {len(test_cases)} 个测试用例")
                    st.dataframe(df.head(10))
            except Exception as e:
                st.error(f"❌ 加载失败：{e}")

        elif use_demo:
            test_cases = [
                {
                    "question": "什么是 Temperature 参数？",
                    "expected_answer": "控制随机性的参数",
                    "category": "基础概念"
                },
                {
                    "question": "如何降低幻觉？",
                    "expected_answer": "使用 RAG、低温度、prompt 约束",
                    "category": "技术方案"
                },
                {
                    "question": "Embedding 是什么？",
                    "expected_answer": "把文字转换为向量",
                    "category": "基础概念"
                },
            ]
            st.success(f"✅ 已加载示例测试集：{len(test_cases)} 个问题")
            st.dataframe(pd.DataFrame(test_cases))

        st.divider()

        # 配置评测选项
        st.subheader("2️⃣ 配置评测选项")

        col1, col2 = st.columns(2)
        with col1:
            use_llm_judge = st.checkbox(
                "启用 LLM-as-judge 评分",
                value=False,
                help="使用大模型对答案质量打分（会增加成本和时间）"
            )
        with col2:
            calculate_hallucination = st.checkbox(
                "计算幻觉检测得分",
                value=True,
                help="检测答案中可能编造的内容"
            )

        # 显示 FastAPI 评测微服务状态（方案 C 的体现）
        if use_llm_judge:
            service_online = st.session_state.judge_client.is_service_available()
            if service_online:
                st.success("🟢 FastAPI 评测微服务在线 - LLM-as-judge 将走独立后端服务")
            else:
                st.warning(
                    "🟡 FastAPI 评测微服务未启动 - 将自动降级到本地调用（功能不受影响）\n\n"
                    "💡 想体验完整的前后端分离架构？运行 `start_all.bat` 同时启动前后端，"
                    "或单独运行 `uvicorn evaluation_service.main:app --port 8001`"
                )

        st.divider()

        # 运行评测
        st.subheader("3️⃣ 运行评测")

        if not test_cases:
            st.info("请先上传测试集或使用示例测试集")
        else:
            run_eval = st.button(
                f"🚀 开始评测（共 {len(test_cases)} 题）",
                type="primary",
                use_container_width=True
            )

            if run_eval:
                # 创建 LLM 客户端
                llm_client = LLMClient()

                # 进度条
                progress_bar = st.progress(0)
                status_text = st.empty()

                # 存储结果
                results = []
                total = len(test_cases)

                for i, test_case in enumerate(test_cases):
                    question = test_case['question']
                    status_text.text(f"正在评测：{i+1}/{total} - {question[:30]}...")

                    try:
                        # 1. 检索
                        retrieved_docs = st.session_state.rag.retrieve(question, top_k=config.TOP_K)

                        if not retrieved_docs:
                            results.append({
                                "question": question,
                                "answer": "",
                                "error": "未找到相关文档",
                                "hallucination_score": None,
                                "llm_judge_score": None,
                            })
                            continue

                        # 2. 生成答案
                        answer, input_tokens, output_tokens = llm_client.answer_question(
                            question,
                            retrieved_docs
                        )

                        # 3. 幻觉检测
                        hallucination_score = None
                        if calculate_hallucination:
                            hallucination_result = st.session_state.hallucination_detector.detect(
                                answer,
                                retrieved_docs
                            )
                            hallucination_score = hallucination_result['score']

                        # 4. LLM-as-judge 评分（优先走 FastAPI 微服务，降级本地）
                        llm_judge_score = None
                        llm_judge_reason = ""
                        llm_judge_mode = None
                        if use_llm_judge:
                            context = "\n\n".join([content for _, content, _ in retrieved_docs])
                            judge_result = st.session_state.judge_client.judge(
                                question,
                                answer,
                                context
                            )
                            llm_judge_score = judge_result.get("score")
                            llm_judge_reason = judge_result.get("reason", "")
                            llm_judge_mode = judge_result.get("mode")

                        # 记录结果
                        result = {
                            "question": question,
                            "answer": answer,
                            "expected_answer": test_case.get("expected_answer", ""),
                            "category": test_case.get("category", ""),
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                            "hallucination_score": hallucination_score,
                            "llm_judge_score": llm_judge_score,
                            "llm_judge_reason": llm_judge_reason,
                            "error": None,
                        }
                        results.append(result)

                        # 短暂延迟，避免限流
                        time.sleep(1)

                    except Exception as e:
                        results.append({
                            "question": question,
                            "answer": "",
                            "error": str(e),
                            "hallucination_score": None,
                            "llm_judge_score": None,
                        })

                    # 更新进度
                    progress_bar.progress((i + 1) / total)

                # 完成
                status_text.text("✅ 评测完成！")
                progress_bar.empty()

                # 保存结果
                st.session_state.evaluation_results = results

                st.success(f"✅ 评测完成！共 {len(results)} 题")
                st.balloons()

    # Tab 2: 评测报告
    with tab2:
        st.header("评测报告")

        if st.session_state.evaluation_results is None:
            st.info("暂无评测结果，请先在「批量评测」标签页运行评测")
        else:
            results = st.session_state.evaluation_results
            df = pd.DataFrame(results)

            # 总体指标
            st.subheader("📊 总体指标")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_count = len(results)
                success_count = len([r for r in results if not r.get('error')])
                st.metric("总测试数", total_count)
                st.metric("成功数", success_count)

            with col2:
                if 'hallucination_score' in df.columns:
                    avg_hallucination = df['hallucination_score'].dropna().mean()
                    st.metric("平均防幻觉得分", f"{avg_hallucination:.0%}")

            with col3:
                if 'llm_judge_score' in df.columns:
                    avg_judge_score = df['llm_judge_score'].dropna().mean()
                    st.metric("平均 LLM-judge 得分", f"{avg_judge_score:.0%}")

            with col4:
                total_tokens = df['input_tokens'].sum() + df['output_tokens'].sum()
                total_cost = sum([
                    config.get_token_cost(config.LLM_MODEL, r['input_tokens'], r['output_tokens'])
                    for r in results if not r.get('error')
                ])
                st.metric("总成本", f"¥{total_cost:.4f}")
                st.metric("总 Tokens", f"{total_tokens:,}")

            st.divider()

            # 详细结果表
            st.subheader("📋 详细结果")

            # 只显示关键列
            display_columns = ['question', 'answer', 'hallucination_score', 'llm_judge_score', 'error']
            display_columns = [col for col in display_columns if col in df.columns]

            st.dataframe(
                df[display_columns],
                use_container_width=True,
                height=400
            )

            # 导出
            st.subheader("💾 导出报告")

            csv = df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 下载 CSV 报告",
                data=csv,
                file_name=f"evaluation_report_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

    # 学习提示
    st.divider()
    st.header("💡 评测体系最佳实践")

    with st.expander("📖 离线评测 vs 在线评测"):
        st.markdown("""
        **离线评测**（本页面）：
        - 准备标准测试集
        - 在开发环境跑评测
        - 快速验证改动效果
        - **优点**：快、可控、可复现
        - **缺点**：测试集可能不够全面

        **在线评测**（真实产品）：
        - 在真实流量上 A/B 测试
        - 收集用户反馈
        - 观察真实指标（采纳率、转化率）
        - **优点**：真实、全面
        - **缺点**：慢、影响用户

        **最佳实践**：
        1. 先离线评测验证方向
        2. 再小流量灰度验证
        3. 最后全量上线
        """)

    with st.expander("📖 LLM-as-judge 的优缺点"):
        st.markdown("""
        **优点**：
        - 自动化、可规模化
        - 不需要人工标注
        - 可以评估"回答质量"这种主观指标

        **缺点**：
        - LLM 自己也可能犯错
        - 增加成本（每个测试用例要调用两次 API）
        - 评分标准可能不稳定

        **适用场景**：
        - 快速迭代阶段，人工标注跟不上
        - 辅助人工评测，快速筛选出问题
        - 大规模评测，人工成本太高

        **注意事项**：
        - LLM-as-judge 的评分要和人工评分对齐
        - 定期抽样人工复核
        - 关键场景（医疗、法律）必须人工确认
        """)


if __name__ == "__main__":
    main()
