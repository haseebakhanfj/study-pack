"""
Streamlit Web Application for AI Study Pack Generator.
Designed for local execution and seamless Streamlit Cloud / GitHub deployment.
"""

import streamlit as st
import os
import json
from workflow import StudyPackWorkflow, WorkflowError

# Page Config
st.set_page_config(
    page_title="AI Study Pack Generator",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for UI styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E88E5; }
    .sub-header { font-size: 1.1rem; color: #555; margin-bottom: 20px; }
    .stMetric { background-color: #f8f9fa; border-radius: 8px; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# Main Title
st.markdown('<div class="main-header">🎓 Multi-Stage AI Study Pack Generator</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Decomposing AI reasoning into Planning → Generation → Assessment → QA Review → Refinement</div>', unsafe_allow_html=True)

# Sidebar Configuration
st.sidebar.title("⚙️ Configuration")

# API Key Handling (Streamlit Secrets or User Input)
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    if "GROQ_API_KEY" in st.secrets:
        api_key = st.secrets["GROQ_API_KEY"]

if not api_key:
    api_key = st.sidebar.text_input("Groq API Key", type="password", help="Enter your Groq API Key to proceed.")
    st.sidebar.info("Tip: Add GROQ_API_KEY to Streamlit Cloud secrets to bypass manual input.")

selected_model = st.sidebar.selectbox(
    "Select Model",
    ["llama-3.3-70b-versatile", "llama3-70b-8192", "mixtral-8x7b-32768"],
    index=0
)

# Initialize Session State for Results
if "study_pack" not in st.session_state:
    st.session_state["study_pack"] = None

# Input Form
with st.form("study_pack_form"):
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Study Topic / Subject", placeholder="e.g., Quantum Computing Basics, Microeconomics")
    with col2:
        target_audience = st.selectbox(
            "Target Audience Level",
            ["High School Student", "Undergraduate", "Postgraduate / Professional", "Beginner General Audience"]
        )
    
    additional_notes = st.text_area(
        "Specific Focus / Instructions (Optional)",
        placeholder="e.g., Emphasize practical applications, include code snippets, or keep explanations intuitive."
    )
    
    submit_btn = st.form_submit_button("🚀 Generate Study Pack", use_container_width=True)

# Workflow Execution Logic
if submit_btn:
    if not api_key:
        st.error("Please provide a valid Groq API Key in the sidebar or app secrets.")
    elif not topic.strip():
        st.warning("Please enter a study topic.")
    else:
        status_box = st.empty()
        progress_bar = st.progress(0)
        
        def update_status(message: str):
            status_box.info(message)

        try:
            workflow = StudyPackWorkflow(api_key=api_key, model=selected_model)
            
            # Execute Pipeline
            progress_bar.progress(20)
            pack = workflow.generate_full_study_pack(
                topic=topic,
                audience=target_audience,
                notes=additional_notes,
                status_callback=update_status
            )
            
            progress_bar.progress(100)
            status_box.success("✅ Study Pack Successfully Generated!")
            st.session_state["study_pack"] = pack

        except WorkflowError as we:
            status_box.empty()
            st.error(f"Workflow Processing Error: {str(we)}")
        except Exception as e:
            status_box.empty()
            st.error(f"Unexpected Error: {str(e)}")

# Display Generated Study Pack
if st.session_state["study_pack"]:
    pack = st.session_state["study_pack"]
    
    st.divider()
    st.subheader("📚 Generated Study Pack")
    
    # Workflow Stage Metadata Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("QA Status", pack["review"].get("status", "N/A"))
    with col2:
        st.metric("QA Quality Score", f"{pack['review'].get('quality_score', 'N/A')}/100")
    with col3:
        st.metric("Refinement Applied", "Yes" if pack.get("refinement_applied") else "No")

    # Render Tabs for Output Inspection
    tab_guide, tab_assessment, tab_plan, tab_qa = st.tabs([
        "📖 Study Guide", 
        "📝 Assessment", 
        "📋 Curriculum Plan", 
        "🔍 QA & Audit Log"
    ])
    
    with tab_guide:
        st.markdown(pack["content"].get("content_markdown", "No content available."))
        
        # Download Markdown Guide
        st.download_button(
            label="💾 Download Study Guide (Markdown)",
            data=pack["content"].get("content_markdown", ""),
            file_name=f"{topic.lower().replace(' ', '_')}_study_guide.md",
            mime="text/markdown"
        )

    with tab_assessment:
        st.subheader("Multiple Choice Questions")
        mcqs = pack["assessment"].get("multiple_choice", [])
        for item in mcqs:
            with st.expander(f"Q{item.get('id')}: {item.get('question')}"):
                st.write("**Options:**")
                for opt in item.get("options", []):
                    st.write(f"- {opt}")
                st.info(f"**Correct Answer:** {item.get('correct_answer')}")
                st.caption(f"**Explanation:** {item.get('explanation')}")

        st.subheader("Reflection Questions")
        reflections = pack["assessment"].get("reflection_questions", [])
        for q in reflections:
            st.write(f"- {q}")

    with tab_plan:
        plan = pack["plan"]
        st.json(plan)

    with tab_qa:
        st.subheader("Quality Assurance Review Details")
        st.json(pack["review"])
        
        if pack.get("refinement_applied"):
            st.subheader("Applied Refinement Fixes")
            for fix in pack.get("refinement_log", []):
                st.write(f"- {fix}")