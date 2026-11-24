from __future__ import annotations

import json
import os
from typing import Any


def get_llm_configuration() -> dict[str, str | None]:
    """Return non-secret LLM configuration details."""
    return {
        "api_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "base_url": os.getenv("OPENAI_BASE_URL") or "OpenAI default",
    }


def generate_heuristic_insights(df, assessment: dict[str, Any]) -> list[str]:
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


def _extract_insights(content: str) -> list[str]:
    content = content.strip()
    if not content:
        return []

    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            parsed = parsed.get("insights", [])
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()][:6]
    except json.JSONDecodeError:
        pass

    return [
        line.strip().lstrip("-*0123456789. ").strip()
        for line in content.splitlines()
        if line.strip()
    ][:6]


def generate_llm_insights(df, assessment: dict[str, Any]) -> list[str] | None:
    """Generate explanations with an OpenAI-compatible Chat Completions API."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI

        client_kwargs: dict[str, Any] = {
            "api_key": api_key,
            "timeout": 30,
        }
        base_url = os.getenv("OPENAI_BASE_URL")
        if base_url:
            client_kwargs["base_url"] = base_url

        client = OpenAI(**client_kwargs)
        prompt_assessment = {
            key: assessment[key]
            for key in (
                "rows",
                "columns",
                "health_score",
                "missing_cells",
                "missing_percentage",
                "duplicate_rows",
                "dtype_issues",
                "highest_missing_columns",
                "outlier_summary",
            )
            if key in assessment
        }
        system_prompt = (
            "You are a careful data-quality analyst. Explain the supplied dataset profile "
            "to a junior analyst in plain English. Include only evidence supported by the "
            "profile. Give 3 to 6 concise, actionable recommendations. "
            'Return a JSON object with an "insights" array of strings.'
        )

        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Dataset profile:\n" + json.dumps(prompt_assessment, ensure_ascii=False),
                },
            ],
        )
        content = response.choices[0].message.content or ""
        return _extract_insights(content) or None
    except Exception as exc:
        print(f"LLM insight generation failed: {exc}")
        return None


def generate_ai_insights(
    df,
    assessment: dict[str, Any],
    use_llm: bool = True,
) -> list[str]:
    """Generate LLM insights when configured, otherwise use local heuristics."""
    if use_llm:
        llm_insights = generate_llm_insights(df, assessment)
        if llm_insights:
            return llm_insights
    return generate_heuristic_insights(df, assessment)
