"""Prompt 版本管理 - 保存、加载、对比不同版本的 Prompt"""
import streamlit as st
import time

import config
from src import PromptManager, LLMClient, HallucinationDetector


def init_session_state():
    """初始化 session state"""
    if 'rag' not in st.session_state:
        from src import load_knowledge_base
        st.session_state.rag = load_knowledge_base()
    if 'prompt_manager' not in st.session_state:
        st.session_state.prompt_manager = PromptManager()
        st.session_state.prompt_manager.initialize_default_prompts()
    if 'hallucination_detector' not in st.session_state:
        st.session_state.hallucination_detector = HallucinationDetector()


def main():
    """主函数"""
    st.set_page_config(**config.STREAMLIT_PAGE_CONFIG)
    init_session_state()

    st.title("📝 Prompt 版本管理")
    st.markdown("""
    **学习目标**：掌握 Prompt 版本化管理、A/B 测试、效果对比

    在这里，你可以：
    - 保存不同版本的 Prompt
    - 对比两个版本在同一问题上的表现
    - 理解 Prompt 微调对效果的影响
    """)

    st.divider()

    # 检查知识库
    if not st.session_state.rag or not st.session_state.rag.documents:
        st.warning("⚠️ 知识库为空，请先在主页加载知识库")
        st.stop()

    # 功能选择
    tab1, tab2, tab3 = st.tabs(["📋 版本列表", "➕ 创建新版本", "⚖️ A/B 对比测试"])

    # Tab 1: 版本列表
    with tab1:
        st.header("已保存的 Prompt 版本")

        prompts = st.session_state.prompt_manager.list_prompts()

        if not prompts:
            st.info("暂无保存的版本，请在「创建新版本」标签页创建")
        else:
            for prompt_info in prompts:
                with st.expander(f"📄 {prompt_info['version_name']} - {prompt_info['description']}"):
                    st.caption(f"创建时间：{prompt_info['created_at']}")

                    # 加载完整信息
                    prompt_data = st.session_state.prompt_manager.load_prompt(prompt_info['version_name'])

                    if prompt_data:
                        st.markdown("**System Prompt:**")
                        st.code(prompt_data['system_prompt'], language="text")

                        st.markdown("**User Prompt Template:**")
                        st.code(prompt_data['user_prompt_template'], language="text")

                        if prompt_data.get('metadata'):
                            st.markdown("**元数据:**")
                            st.json(prompt_data['metadata'])

                        # 删除按钮
                        if st.button(f"🗑️ 删除版本", key=f"delete_{prompt_info['version_name']}"):
                            if st.session_state.prompt_manager.delete_prompt(prompt_info['version_name']):
                                st.success("已删除")
                                st.rerun()

    # Tab 2: 创建新版本
    with tab2:
        st.header("创建新的 Prompt 版本")

        version_name = st.text_input(
            "版本名称",
            placeholder="例如：v4_medical",
            help="建议使用语义化命名，如 v1, v2_strict, v3_friendly"
        )

        description = st.text_area(
            "版本描述",
            placeholder="描述这个版本的特点、改进点、适用场景",
            height=80
        )

        system_prompt = st.text_area(
            "System Prompt",
            value=config.DEFAULT_SYSTEM_PROMPT,
            height=300,
            help="定义 AI 的身份、规则、边界"
        )

        user_prompt_template = st.text_area(
            "User Prompt Template",
            value=config.USER_PROMPT_TEMPLATE,
            height=200,
            help="使用 {context} 和 {question} 作为占位符"
        )

        # 元数据
        st.markdown("**元数据（可选）**")
        col1, col2 = st.columns(2)
        with col1:
            适用场景 = st.text_input("适用场景", placeholder="例如：医疗咨询")
        with col2:
            特点 = st.text_input("特点", placeholder="例如：极低幻觉率")

        metadata = {
            "适用场景": 适用场景,
            "特点": 特点,
        }

        # 保存
        if st.button("💾 保存版本", type="primary"):
            if not version_name:
                st.error("请输入版本名称")
            else:
                success = st.session_state.prompt_manager.save_prompt(
                    version_name=version_name,
                    system_prompt=system_prompt,
                    user_prompt_template=user_prompt_template,
                    description=description,
                    metadata=metadata
                )
                if success:
                    st.success(f"✅ 版本 {version_name} 已保存")
                    st.balloons()

    # Tab 3: A/B 对比测试
    with tab3:
        st.header("A/B 对比测试")
        st.markdown("选择两个版本，用同一个问题测试，对比效果")

        # 获取版本列表
        prompts = st.session_state.prompt_manager.list_prompts()

        if len(prompts) < 2:
            st.warning("至少需要 2 个版本才能进行 A/B 对比")
            st.stop()

        version_names = [p['version_name'] for p in prompts]

        # 选择版本
        col1, col2 = st.columns(2)
        with col1:
            version_a = st.selectbox("选择版本 A", version_names, key="version_a_select")
        with col2:
            version_b = st.selectbox("选择版本 B", version_names, index=min(1, len(version_names)-1), key="version_b_select")

        # 输入问题
        test_question = st.text_input(
            "测试问题",
            placeholder="例如：什么是 RAG？",
            key="ab_test_question"
        )

        run_ab_test = st.button("🚀 运行 A/B 测试", type="primary", use_container_width=True)

        # 运行测试
        if run_ab_test and test_question:
            if version_a == version_b:
                st.warning("请选择不同的版本")
                st.stop()

            st.divider()
            st.subheader("📊 测试结果")

            # 检索文档（两组共用）
            with st.spinner("🔍 检索知识库..."):
                retrieved_docs = st.session_state.rag.retrieve(test_question, top_k=config.TOP_K)

                if not retrieved_docs:
                    st.warning("❌ 未找到相关内容")
                    st.stop()

            # 加载两个版本的 prompt
            prompt_data_a = st.session_state.prompt_manager.load_prompt(version_a)
            prompt_data_b = st.session_state.prompt_manager.load_prompt(version_b)

            col1, col2 = st.columns(2)

            # 版本 A
            with col1:
                st.subheader(f"🅰️ {version_a}")
                st.caption(prompt_data_a['description'])

                with st.spinner("生成中..."):
                    start_time = time.time()

                    client = LLMClient()
                    answer_a, input_tokens_a, output_tokens_a = client.answer_question(
                        test_question,
                        retrieved_docs,
                        system_prompt=prompt_data_a['system_prompt'],
                        user_prompt_template=prompt_data_a['user_prompt_template']
                    )

                    response_time_a = time.time() - start_time

                # 幻觉检测
                hallucination_a = st.session_state.hallucination_detector.detect(
                    answer_a,
                    retrieved_docs
                )

                # 显示
                st.info(answer_a)
                st.metric("响应时间", f"{response_time_a:.2f}秒")
                st.metric("防幻觉得分", f"{hallucination_a['score']:.0%}")
                st.metric("输出 tokens", output_tokens_a)

            # 版本 B
            with col2:
                st.subheader(f"🅱️ {version_b}")
                st.caption(prompt_data_b['description'])

                with st.spinner("生成中..."):
                    start_time = time.time()

                    client = LLMClient()
                    answer_b, input_tokens_b, output_tokens_b = client.answer_question(
                        test_question,
                        retrieved_docs,
                        system_prompt=prompt_data_b['system_prompt'],
                        user_prompt_template=prompt_data_b['user_prompt_template']
                    )

                    response_time_b = time.time() - start_time

                # 幻觉检测
                hallucination_b = st.session_state.hallucination_detector.detect(
                    answer_b,
                    retrieved_docs
                )

                # 显示
                st.info(answer_b)
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
                    "防幻觉得分",
                    f"{abs(diff):.0%}",
                    delta=f"{version_a if diff > 0 else version_b if diff < 0 else '相同'}"
                )
            with col2:
                diff_tokens = output_tokens_a - output_tokens_b
                st.metric(
                    "输出长度",
                    abs(diff_tokens),
                    delta=f"{version_a if diff_tokens > 0 else version_b if diff_tokens < 0 else '相同'}"
                )
            with col3:
                diff_time = response_time_a - response_time_b
                st.metric(
                    "速度",
                    f"{abs(diff_time):.2f}秒",
                    delta=f"{version_a if diff_time < 0 else version_b if diff_time < 0 else '相同'}"
                )

    # 学习提示
    st.divider()
    st.header("💡 Prompt 版本管理最佳实践")

    with st.expander("📖 为什么要做版本管理？"):
        st.markdown("""
        **Prompt 改一个字，效果可能天差地别。**

        版本管理的价值：
        1. **可追溯**：知道每个版本改了什么、为什么改
        2. **可对比**：通过 A/B 测试验证改进效果
        3. **可回滚**：如果新版本效果不好，可以回到旧版本
        4. **团队协作**：多人协作时，有统一的版本记录

        **在真实产品中**：
        - 每次 Prompt 改动都要记录版本号和改动原因
        - 新版本要跑完整测试集，对比准确率
        - 线上灰度发布，观察真实用户数据
        """)

    with st.expander("📖 如何做好 A/B 测试？"):
        st.markdown("""
        **A/B 测试的关键：**

        1. **单变量原则**：一次只改一个点（如加强"不能编造"的约束），不要同时改多个
        2. **标准测试集**：准备一批典型问题，每次改版都跑一遍
        3. **多维度评估**：不只看准确率，还要看拒答率、用户体验、成本
        4. **真实流量验证**：离线测试好了，还要在真实流量上灰度验证

        **本项目的 A/B 测试流程：**
        1. 创建新版本 Prompt
        2. 在这个页面对比两个版本
        3. 去"评测中心"跑完整测试集
        4. 去"运营看板"看整体指标
        """)


if __name__ == "__main__":
    main()
