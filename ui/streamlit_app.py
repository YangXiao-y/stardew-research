import streamlit as st
from core.research_flow_factory import get_research_flow
from autogen_config import get_all_available_models


def run_ui():
    st.set_page_config(page_title="Stardew Deep Research", layout="wide")
    st.title("🌾 Stardew Valley Deep Research Assistant")

    # 侧边栏配置
    st.sidebar.header("⚙️ 配置")

    mode = st.sidebar.radio(
        "选择研究模式",
        ["AutoGen (新)", "LangChain (旧)"],
        help="AutoGen: 基于新框架 | LangChain: 原始实现"
    )

    flow_mode = "autogen" if mode.startswith("AutoGen") else "legacy"

    # 根据模式选择模型
    if flow_mode == "autogen":
        available_models = get_all_available_models()
        model = st.sidebar.selectbox(
            "选择LLM模型",
            available_models,
            help="选择使用的大语言模型"
        )
    else:
        model = "qwen"

    debug_mode = st.sidebar.checkbox(
        "调试模式",
        value=False,
        help="启用详细的执行日志"
    )

    # 主界面
    question = st.text_area(
        "输入问题",
        placeholder="例如：第一年如何兼顾社区中心和赚钱？"
    )

    if st.button("🔍 开始研究") and question.strip():
        try:
            # 获取研究流程实例
            flow = get_research_flow(mode=flow_mode, model=model, debug=debug_mode)

            with st.spinner(f"系统正在进行 Deep Research ({mode})..."):
                state = flow.run(question)

            # 展示结果
            st.success("✅ 研究完成！")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("问题类型")
                st.code(state.question_type)

                st.subheader(f"任务拆解 ({len(state.subtasks)} 个)")
                st.json([x.model_dump() for x in state.subtasks[:5]])

                st.subheader("缺口分析")
                if state.missing_points:
                    st.json(state.missing_points)
                else:
                    st.info("✓ 无缺口")

            with col2:
                st.subheader(f"证据池 ({len(state.evidence_pool)} 项)")
                st.json([x.model_dump() for x in state.evidence_pool[:10]])

            st.subheader("📝 最终结果")
            st.markdown(state.final_answer)

            # 显示研究统计信息
            st.divider()
            st.subheader("📊 研究统计")
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("任务数", len(state.subtasks))
            col2.metric("证据数", len(state.evidence_pool))
            col3.metric("研究轮次", state.round_id)
            col4.metric("答案长度", f"{len(state.final_answer)} 字")

        except Exception as e:
            st.error(f"❌ 研究过程中出错：{str(e)}")
            st.exception(e)