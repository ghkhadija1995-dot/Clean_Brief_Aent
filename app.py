"""
app.py
------
واجهة Streamlit لوكيل CleanBrief - تنظيف وتحليل البيانات.
"""

import os
import streamlit as st
from CleanBrief_Agent import run_agent

# ---------------------------------------------------------------
# إعدادات الصفحة العامة
# ---------------------------------------------------------------
st.set_page_config(
    page_title="CleanBrief Agent",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# تنسيق بسيط لتحسين الشكل (خطوط، مسافات، بطاقات)
st.markdown(
    """
    <style>
        .main .block-container {padding-top: 2rem; padding-bottom: 3rem;}
        div[data-testid="stMetric"] {
            background-color: rgba(148, 163, 184, 0.08);
            border: 1px solid rgba(148, 163, 184, 0.2);
            border-radius: 12px;
            padding: 14px 16px;
        }
        .stTabs [data-baseweb="tab"] {font-size: 15px; font-weight: 600;}
        h1, h2, h3 {font-weight: 700;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# الشريط الجانبي: مفتاح الـ API + الإعدادات
# ---------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ الإعدادات")
    api_key = st.text_input("مفتاح OpenAI API", type="password", placeholder="sk-...")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    st.divider()
    st.caption(
        "ارفع ملف CSV أو Excel، واكتب سؤالك (اختياري)، "
        "وسيقوم الوكيل بفحص جودة البيانات وتنظيفها وكتابة تقرير تنفيذي."
    )

# ---------------------------------------------------------------
# رأس الصفحة
# ---------------------------------------------------------------
st.title("🧹📋CleanBrief Agent")
st.caption("نظّف بياناتك، افحص جودتها، واحصل على تقرير تنفيذي جاهز للعرض في دقائق.")

# ---------------------------------------------------------------
# منطقة الإدخال
# ---------------------------------------------------------------
col_upload, col_question = st.columns([1, 1])

with col_upload:
    uploaded_file = st.file_uploader("📁 ارفع ملف البيانات", type=["csv", "xlsx", "xls"])

with col_question:
    question = st.text_area(
        "❓ سؤالك عن الملف (اختياري)",
        placeholder="مثال: كم عدد حالات الوفاة في الملف؟",
        height=110,
    )

run_clicked = st.button("🚀 تشغيل التحليل", type="primary", use_container_width=True)

# ---------------------------------------------------------------
# التشغيل وعرض المخرجات بشكل منظم
# ---------------------------------------------------------------
if run_clicked:
    if not api_key:
        st.error("الرجاء إدخال مفتاح OpenAI API في الشريط الجانبي أولاً.")
    elif not uploaded_file:
        st.error("الرجاء رفع ملف CSV أو Excel أولاً.")
    else:
        # حفظ الملف المرفوع مؤقتاً على القرص
        temp_path = os.path.join("temp_uploads", uploaded_file.name)
        os.makedirs("temp_uploads", exist_ok=True)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        with st.spinner("جاري فحص جودة البيانات وتنظيفها واستشارة المستشار الذكي..."):
            result = run_agent(temp_path, question)

        if not result["ok"]:
            st.error(result["error"])
        else:
            st.success("تم التحليل بنجاح ✅")

            # --- بطاقات المؤشرات في الأعلى ---
            st.subheader("📊 مؤشرات الجودة")
            metric_cols = st.columns(len(result["metrics"]))
            for col, (label, value) in zip(metric_cols, result["metrics"].items()):
                col.metric(label, value)

            st.divider()

            # --- تبويبات منظمة للنتائج ---
            tab_summary, tab_actions, tab_data = st.tabs(
                ["📋 الخلاصة التنفيذية", "🚀 التوصيات", "🔎 عينة البيانات النظيفة"]
            )

            with tab_summary:
                st.write(result["summary"])

            with tab_actions:
                for i, action in enumerate(result["recommendations"], start=1):
                    st.markdown(f"**{i}.** {action}")

            with tab_data:
                st.dataframe(result["data_sample"], use_container_width=True)

            st.divider()

            # --- تحميل الملف النظيف ---
            with open(result["cleaned_path"], "rb") as f:
                st.download_button(
                    label="⬇️ تحميل الملف النظيف",
                    data=f,
                    file_name=os.path.basename(result["cleaned_path"]),
                    use_container_width=True,
                )
