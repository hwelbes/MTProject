from __future__ import annotations

from typing import Any


def generate_ai_insights(df, assessment: dict[str, Any]) -> list[str]:
    """Turn profile metrics into plain-English recommendations using heuristic logic."""
    insights: list[str] = []

    if assessment["duplicate_rows"]:
        insights.append(
            f"The dataset contains {assessment['duplicate_rows']} duplicate rows. Removing them will reduce noise and improve the quality score before further analysis."
        )

    highest_missing = assessment["highest_missing_columns"]
    if highest_missing:
        column, pct = highest_missing[0]
        insights.append(
            f"{column} is the most incomplete field, with {pct}% missing values. Consider a review of its source data or a targeted imputation strategy before modeling."
        )

    dtype_issues = assessment["dtype_issues"]
    if dtype_issues:
        issues_text = ", ".join(dtype_issues[:3])
        insights.append(
            f"Several columns appear to hold numeric values but may be stored as text, including {issues_text}. Converting them to numeric types may improve aggregation and validation accuracy."
        )

    outlier_summary = assessment["outlier_summary"]
    if outlier_summary:
        highest_outlier = max(outlier_summary.items(), key=lambda item: item[1]["percent"])
        column, details = highest_outlier
        if details["percent"] > 0:
            insights.append(
                f"{column} shows {details['percent']}% outlier values, which may reflect entry errors or unusual transactions worth validating."
            )

    if not insights:
        insights.append(
            "The dataset is relatively healthy at the moment. Continue monitoring for drift, schema changes, and category-level anomalies during future uploads."
        )

    return insights
