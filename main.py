"""AI 智能问答助手 - 主应用"""
import time
import streamlit as st

import config
from src import (
    load_knowledge_base,
    LLMClient,
    PromptManager,
    HallucinationDetector,
    Analytics
)


def init_session_state():
    """初始化 session state"""
    if 'rag' not in st.session_state:
        st.session_state.rag = None
    if 'llm_client' not in st.session_state:
        st.session_state.llm_client = None
    if 'prompt_manager' not in st.session_state:
        st.session_state.prompt_manager = PromptManager()
        st.session_state.prompt_manager.initialize_default_prompts()
    if 'hallucination_detector' not in st.session_state:
        st.session_state.hallucination_detector = HallucinationDetector()
    if 'analytics' not in st.session_state:
        st.session_state.analytics = Analytics()
    if 'current_result' not in st.session_state:
        st.session_state.current_result = None
    if 'user_feedback' not in st.session_state:
        st.session_state.user_feedback = {}


@st.cache_resource
def load_rag_engine():
    """加载 RAG 引擎（缓存，只加载一次）"""
    return load_knowledge_base()


def main():
    """主函数"""
    # 页面配置
    st.set_page_config(**config.STREAMLIT_PAGE_CONFIG)

    # 初始化
    init_session_state()

    # 标题
    st.title("🤖 AI 智能问答助手")
    st.markdown("""
    **学习目标**：掌握 AI 产品经理的核心技能 - 从语义检索、参数调优到评测体系

    ---
    """)

    # 侧边栏
    with st.sidebar:
        st.header("📚 功能导航")
        st.page_link("main.py", label="🏠 智能问答", icon="🏠")
        st.page_link("pages/1_参数调优实验室.py", label="🎛️ 参数调优实验室", icon="🎛️")
        st.page_link("pages/2_Prompt版本管理.py", label="📝 Prompt 版本管理", icon="📝")
        st.page_link("pages/3_评测中心.py", label="📊 评测中心", icon="📊")
        st.page_link("pages/4_运营看板.py", label="📈 运营看板", icon="📈")
        st.page_link("pages/5_成本与延迟仪表盘.py", label="💰 成本与延迟仪表盘", icon="💰")
        st.page_link("pages/6_FunctionCalling演示.py", label="🛠️ Function Calling 演示", icon="🛠️")

        st.divider()

        st.header("⚙️ 系统状态")

        # 检查 API Key
        if not config.LLM_API_KEY:
            st.error("⚠️ 未配置 API Key")
            st.info("请复制 `.env.example` 为 `.env` 并填入你的 API 密钥")
            st.stop()
        else:
            st.success("✅ API Key 已配置")

        # 显示当前配置
        st.info(f"""
        **模型**: {config.LLM_MODEL}
        **温度**: {config.LLM_TEMPERATURE}
        **检索 TOP_K**: {config.TOP_K}
        """)

    # 加载 RAG 引擎
    if st.session_state.rag is None:
        with st.spinner("🔄 首次启动，正在加载知识库和向量索引..."):
            try:
                st.session_state.rag = load_rag_engine()

                # 检查是否有知识库
                if not st.session_state.rag.documents:
                    st.warning("⚠️ 知识库为空，请在 `data/knowledge_base/` 目录下添加 .txt 文件")
                    st.info("""
                    **如何添加知识库文档：**
                    1. 在 `data/knowledge_base/` 目录下创建 .txt 文件
                    2. 每个文件是一个主题的知识文档
                    3. 文件名作为文档名称显示
                    4. 重启应用，系统会自动构建向量索引
                    """)
                else:
                    st.success(f"✅ 知识库已加载：{len(st.session_state.rag.documents)} 个文档")
            except Exception as e:
                st.error(f"❌ 加载失败：{e}")
                st.stop()

    # 初始化 LLM 客户端
    if st.session_state.llm_client is None:
        st.session_state.llm_client = LLMClient()

    # 主界面
    st.header("💬 智能问答")

    # 输入区
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input(
            "请输入您的问题：",
            placeholder="例如：什么是 Temperature 参数？如何调节温度参数？",
            key="question_input"
        )
    with col2:
        st.write("")  # 对齐
        submit = st.button("🔍 提问", type="primary", use_container_width=True)

    # 处理提问
    if submit and question:
        # 记录开始时间
        start_time = time.time()

        with st.spinner("🔍 检索知识库..."):
            try:
                # 1. 检索相关文档
                retrieved_docs = st.session_state.rag.retrieve(question, top_k=config.TOP_K)

                if not retrieved_docs:
                    st.warning("❌ 未找到相关内容，请尝试换个问法或添加相关文档到知识库")
                    st.stop()

                # 2. 调用 LLM 生成回答
                with st.spinner("🤖 AI 思考中..."):
                    answer, input_tokens, output_tokens = st.session_state.llm_client.answer_question(
                        question,
                        retrieved_docs
                    )

                # 3. 幻觉检测
                hallucination_result = st.session_state.hallucination_detector.detect(
                    answer,
                    retrieved_docs
                )

                # 4. 分类
                category, category_note = st.session_state.hallucination_detector.classify_answer(
                    answer,
                    hallucination_result
                )

                # 计算响应时间
                response_time = time.time() - start_time

                # 5. 记录日志
                st.session_state.analytics.log_interaction(
                    question=question,
                    answer=answer,
                    retrieved_docs=retrieved_docs,
                    hallucination_result=hallucination_result,
                    model=config.LLM_MODEL,
                    temperature=config.LLM_TEMPERATURE,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    response_time=response_time
                )

                # 6. 存储结果
                st.session_state.current_result = {
                    "question": question,
                    "answer": answer,
                    "retrieved_docs": retrieved_docs,
                    "hallucination_result": hallucination_result,
                    "category": category,
                    "category_note": category_note,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "response_time": response_time,
                }

            except Exception as e:
                st.error(f"❌ 出错了：{e}")
                st.stop()

    # 显示结果
    if st.session_state.current_result:
        result = st.session_state.current_result

        st.success("✅ 回答生成完毕")

        # 显示答案
        st.markdown("### 💬 AI 回答")

        # 根据风险等级显示不同样式
        if result["category"] == "refusal":
            st.warning(result["answer"])
        elif result["category"] == "high_risk":
            st.error(f"⚠️ 高风险回答\n\n{result['answer']}")
        else:
            st.info(result["answer"])

        # 显示指标
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("响应时间", f"{result['response_time']:.2f}秒")
        with col2:
            st.metric("防幻觉得分", f"{result['hallucination_result']['score']:.0%}")
        with col3:
            st.metric("Token 消耗", result['input_tokens'] + result['output_tokens'])
        with col4:
            cost = config.get_token_cost(
                config.LLM_MODEL,
                result['input_tokens'],
                result['output_tokens']
            )
            st.metric("成本", f"¥{cost:.4f}")

        # 显示风险提示
        risk_level = result['hallucination_result']['risk_level']
        if risk_level == "high":
            st.error("⚠️ **高风险警告**：此回答中大量关键词无法在原文档中找到依据，可能存在较多编造内容")
        elif risk_level == "medium":
            st.warning("⚠️ **中风险提示**：此回答中部分关键词无法在原文档中找到依据，请谨慎采纳")

        # 用户反馈
        st.markdown("### 📋 这个回答对你有帮助吗？")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 有用", key=f"useful_{result['question'][:20]}"):
                # 更新日志（这里简化处理，实际应该更新最后一条日志）
                st.success("感谢反馈！")
        with col2:
            if st.button("👎 没用", key=f"not_useful_{result['question'][:20]}"):
                st.info("感谢反馈，我们会继续改进")

        # 显示检索的文档
        with st.expander("📚 查看引用文档"):
            for i, (doc_name, content, score) in enumerate(result["retrieved_docs"], 1):
                st.markdown(f"**[文档 {i}] {doc_name}** (相似度: {score:.3f})")
                st.text(content)
                st.divider()

        # 显示幻觉检测详情
        with st.expander("🔍 幻觉检测详情"):
            detail = result["hallucination_result"]
            st.write(f"**总关键词数**: {detail['total_keywords']}")
            st.write(f"**有文档支撑**: {detail['supported_keywords']} ({detail['score']:.0%})")
            st.write(f"**无文档支撑**: {len(detail['unsupported_keywords'])}")

            if detail['unsupported_keywords']:
                st.warning(f"**无依据的关键词**：{', '.join(detail['unsupported_keywords'][:20])}")

            st.write(f"**所有关键词**：{', '.join(detail['all_keywords'][:30])}")

    # 页脚
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: gray; font-size: 0.9em;'>
    📖 这是一个 AI 产品经理学习项目 |
    <a href='https://github.com' target='_blank'>GitHub</a> |
    通过实践掌握 RAG、Prompt、评测的全流程
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
