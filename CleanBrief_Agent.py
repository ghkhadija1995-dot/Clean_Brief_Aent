"""
CleanBrief_Agent.py
--------------------
المنطق الخلفي (Backend) لوكيل تنظيف وتحليل البيانات.
يوفّر دالة واحدة رئيسية run_agent() تستدعيها واجهة Streamlit.
"""

import os
import pandas as pd
from typing import List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI


class StrategicReport(BaseModel):
    executive_summary: str = Field(description="خلاصة تنفيذية للمدراء عن أداء الأعمال بناءً على البيانات.")
    recommended_actions: List[str] = Field(description="توصيات استراتيجية بناءً على الأرقام النظيفة فقط.")


def clean_and_profile_data(file_path: str) -> dict:
    """يقرأ الملف، يحسب مؤشرات الجودة، ينظف البيانات، ويحفظ نسخة جديدة."""
    if not os.path.exists(file_path):
        return {"error": f"الملف {file_path} غير موجود."}

    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file_path)
    else:
        return {"error": "صيغة الملف غير مدعومة للتنظيف الإحصائي حالياً."}

    initial_rows = len(df)
    missing_values = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].mean())
        else:
            df[col] = df[col].fillna("غير متوفر")
    df = df.drop_duplicates()

    base_name, ext = os.path.splitext(file_path)
    cleaned_file_path = f"{base_name}_cleaned{ext}"
    if ext == ".csv":
        df.to_csv(cleaned_file_path, index=False)
    else:
        df.to_excel(cleaned_file_path, index=False)

    return {
        "cleaned_path": cleaned_file_path,
        "cleaned_df": df,
        "metrics": {
            "إجمالي الأسطر قبل التنظيف": initial_rows,
            "إجمالي الأسطر بعد التنظيف": len(df),
            "القيم المفقودة المعبأة تلقائياً": missing_values,
            "الصفوف المكررة المحذوفة": duplicate_rows,
        },
        "data_sample": df.head(5),
    }


def run_agent(file_path: str, question: str = "") -> dict:
    """
    نقطة الدخول الرئيسية التي تستدعيها الواجهة (app.py).
    ترجع قاموساً منظماً يحتوي على كل ما تحتاجه الواجهة لعرض النتائج بشكل مرتب:
    {
        "ok": bool,
        "error": str | None,
        "summary": str,
        "recommendations": List[str],
        "metrics": dict,
        "data_sample": DataFrame,
        "cleaned_path": str,
    }
    """
    if not question:
        question = "أعطني ملخصاً لأداء الشركة بناءً على هذا الملف وما هي التوصيات المبدئية؟"

    report = clean_and_profile_data(file_path)
    if "error" in report:
        return {"ok": False, "error": report["error"]}

    llm = ChatOpenAI(model="gpt-4o", temperature=0.1)
    structured_llm = llm.with_structured_output(StrategicReport)

    prompt = [
        {
            "role": "system",
            "content": (
                "أنت مستشار تنفيذي متخصص في تحليل جودة البيانات. اكتب خلاصة تنفيذية "
                "وتوصيات استراتيجية بناءً على مؤشرات التنظيف والعينة المرفقة فقط، "
                "دون اختراع أرقام جديدة."
            ),
        },
        {
            "role": "user",
            "content": (
                f"سؤال المستخدم: {question}\n\n"
                f"مؤشرات التنظيف: {report['metrics']}\n\n"
                f"عينة من البيانات النظيفة:\n{report['data_sample'].to_string()}"
            ),
        },
    ]
    llm_out = structured_llm.invoke(prompt)

    return {
        "ok": True,
        "error": None,
        "summary": llm_out.executive_summary,
        "recommendations": llm_out.recommended_actions,
        "metrics": report["metrics"],
        "data_sample": report["data_sample"],
        "cleaned_path": report["cleaned_path"],
    }
