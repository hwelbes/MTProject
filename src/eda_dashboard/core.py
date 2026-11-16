from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def load_dataset(uploaded_file) -> pd.DataFrame:
    """Load a CSV or Excel file uploaded through Streamlit."""
    filename = getattr(uploaded_file, "name", "")
    if filename.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    raise ValueError("Unsupported file type. Upload a CSV or Excel file.")


def _safe_mode(series: pd.Series) -> Any:
    mode = series.mode(dropna=True)
    return mode.iloc[0] if not mode.empty else None


def assess_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    """Generate a description of data quality issues and a health score."""
    total_cells = df.size
    missing_cells = int(df.isna().sum().sum())
    missing_pct = (missing_cells / total_cells * 100) if total_cells else 0.0
    duplicate_rows = int(df.duplicated().sum())

    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    outlier_summary: dict[str, Any] = {}
    for column in numeric_columns:
        series = df[column].dropna()
        if series.empty:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        outliers = series[(series < lower_bound) | (series > upper_bound)]
        outlier_summary[column] = {
            "count": int(outliers.shape[0]),
            "percent": round((outliers.shape[0] / series.shape[0]) * 100, 2) if series.shape[0] else 0.0,
        }

    dtype_issues: list[str] = []
    for column in df.columns:
        series = df[column]
        non_null = series.dropna()
        if non_null.empty:
            continue
        inferred_numeric = pd.api.types.is_numeric_dtype(non_null)
        if not inferred_numeric and series.map(lambda value: isinstance(value, str) and value.strip() != "").all():
            sample_values = non_null.head(10).astype(str)
            numeric_like = sample_values.str.fullmatch(r"[-+]?\d+(?:\.\d+)?")
            if numeric_like.all():
                dtype_issues.append(column)

    missing_by_column = df.isna().mean().mul(100).round(2).to_dict()
    highest_missing = sorted(missing_by_column.items(), key=lambda item: item[1], reverse=True)[:5]

    issue_penalty = 0
    issue_penalty += min(25, duplicate_rows * 2)
    issue_penalty += min(25, sum(1 for pct in missing_by_column.values() if pct > 10) * 5)
    issue_penalty += min(20, len(dtype_issues) * 5)
    issue_penalty += min(15, sum(1 for value in outlier_summary.values() if value["percent"] > 10) * 5)

    health_score = max(0, 100 - issue_penalty)

    return {
        "shape": df.shape,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "health_score": int(health_score),
        "missing_cells": missing_cells,
        "missing_percentage": round(missing_pct, 2),
        "duplicate_rows": duplicate_rows,
        "dtype_issues": dtype_issues,
        "missing_by_column": missing_by_column,
        "highest_missing_columns": highest_missing,
        "outlier_summary": outlier_summary,
        "column_types": {column: str(dtype) for column, dtype in df.dtypes.items()},
    }


def clean_dataframe(df: pd.DataFrame, remove_duplicates: bool = True, fill_missing: bool = True) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Apply default cleaning steps and return the cleaned frame plus a summary."""
    cleaned = df.copy()
    summary: dict[str, Any] = {
        "removed_duplicates": 0,
        "missing_values_filled": 0,
        "columns_standardized": 0,
    }

    cleaned.columns = [str(column).strip() for column in cleaned.columns]
    cleaned.columns = [column.replace(" ", "_").lower() for column in cleaned.columns]
    summary["columns_standardized"] = len(cleaned.columns)

    if remove_duplicates:
        before = len(cleaned)
        cleaned = cleaned.drop_duplicates().reset_index(drop=True)
        summary["removed_duplicates"] = before - len(cleaned)

    for column in cleaned.columns:
        if cleaned[column].dtype == "object":
            cleaned[column] = cleaned[column].astype(str).str.strip()
            cleaned[column] = cleaned[column].replace({"nan": np.nan, "None": np.nan, "": np.nan})

    if fill_missing:
        for column in cleaned.columns:
            missing_before = int(cleaned[column].isna().sum())
            if missing_before == 0:
                continue
            if pd.api.types.is_numeric_dtype(cleaned[column]):
                fill_value = cleaned[column].median()
                cleaned[column] = cleaned[column].fillna(fill_value)
            else:
                fill_value = _safe_mode(cleaned[column].dropna())
                cleaned[column] = cleaned[column].fillna(fill_value)
            summary["missing_values_filled"] += missing_before

    return cleaned, summary
