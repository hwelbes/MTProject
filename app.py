from __future__ import annotations

import io

import pandas as pd
import streamlit as st

from src.eda_dashboard.core import assess_dataframe, clean_dataframe, load_dataset
from src.eda_dashboard.insights import generate_ai_insights, get_llm_configuration

st.set_page_config(page_title="EDA & Cleaning Dashboard", layout="wide")
st.title("Automated Exploratory Data Analysis & Cleaning Dashboard")
st.caption("Upload a CSV or Excel file to profile, score, and clean it in a single workflow.")

with st.sidebar:
    st.header("Dataset Controls")
    remove_duplicates = st.checkbox("Remove duplicate rows", value=True)
    fill_missing = st.checkbox("Fill missing values automatically", value=True)
    use_llm = st.checkbox("Use LLM for explanations", value=True)
    st.markdown("---")
    st.caption("Built for junior analysts, BI students, and research teams.")

uploaded_file = st.file_uploader("Upload your dataset", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    try:
        df = load_dataset(uploaded_file)
    except ValueError as exc:
        st.error(str(exc))
        st.stop()

    assessment = assess_dataframe(df)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Rows", assessment["rows"])
    col2.metric("Columns", assessment["columns"])
    col3.metric("Missing Cells", assessment["missing_cells"])
    col4.metric("Health Score", f"{assessment['health_score']}/100")

    quality_tab, preview_tab, insights_tab = st.tabs(["Quality Overview", "Dataset Preview", "AI Insights"])

    with quality_tab:
        st.subheader("Data Quality Summary")
        st.write(
            "This score blends missing-value pressure, duplicate records, type issues, and outlier volume into a single quality assessment."
        )
        st.progress(assessment["health_score"] / 100)

        summary_df = pd.DataFrame(
            [
                {"Check": "Duplicate rows", "Value": assessment["duplicate_rows"]},
                {"Check": "Missing cells", "Value": assessment["missing_cells"]},
                {"Check": "Missing %", "Value": f"{assessment['missing_percentage']}%"},
                {"Check": "Columns with type issues", "Value": len(assessment["dtype_issues"])},
            ]
        )
        st.dataframe(summary_df, use_container_width=True)

        if assessment["missing_by_column"]:
            missing_df = pd.DataFrame(
                {
                    "Column": list(assessment["missing_by_column"].keys()),
                    "Missing %": list(assessment["missing_by_column"].values()),
                }
            ).sort_values("Missing %", ascending=False)
            st.subheader("Missing Value Profile")
            st.dataframe(missing_df, use_container_width=True)

        if assessment["outlier_summary"]:
            outlier_df = pd.DataFrame(
                [
                    {"Column": column, "Outlier %": details["percent"], "Outlier count": details["count"]}
                    for column, details in assessment["outlier_summary"].items()
                ]
            )
            st.subheader("Outlier Snapshot")
            st.dataframe(outlier_df, use_container_width=True)

    with preview_tab:
        st.subheader("Original Dataset")
        st.dataframe(df.head(25), use_container_width=True)
        cleaned_df, cleaning_summary = clean_dataframe(df, remove_duplicates=remove_duplicates, fill_missing=fill_missing)
        st.subheader("Cleaned Dataset")
        st.dataframe(cleaned_df.head(25), use_container_width=True)

        st.caption(
            "Cleaning summary: "
            f"{cleaning_summary['removed_duplicates']} duplicate rows removed; "
            f"{cleaning_summary['columns_standardized']} columns standardized; "
            f"{cleaning_summary['missing_values_filled']} missing values filled."
        )

        buffer = io.StringIO()
        cleaned_df.to_csv(buffer, index=False)
        st.download_button(
            label="Download cleaned CSV",
            data=buffer.getvalue(),
            file_name="cleaned_dataset.csv",
            mime="text/csv",
        )

    with insights_tab:
        st.subheader("AI-Powered Recommendations")
        llm_config = get_llm_configuration()
        if use_llm and llm_config["api_key_configured"]:
            st.caption(f"LLM: {llm_config['model']}")
        elif use_llm:
            st.warning(
                "LLM API is not configured. Set OPENAI_API_KEY and optionally "
                "OPENAI_MODEL or OPENAI_BASE_URL. Showing local recommendations instead."
            )

        insights = generate_ai_insights(df, assessment, use_llm=use_llm)
        for insight in insights:
            st.markdown(f"- {insight}")

        if not assessment["dtype_issues"] and not assessment["highest_missing_columns"] and assessment["duplicate_rows"] == 0:
            st.success("No major issues detected. You are ready to move into analysis or modeling.")
else:
    st.info("Upload a CSV or Excel file to begin the automated EDA and cleaning workflow.")
    st.markdown(
        """
        Suggested demo data includes:
        - Customer transaction history
        - Research survey responses
        - CRM event logs
        """
    )
