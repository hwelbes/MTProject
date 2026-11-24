from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from src.eda_dashboard.insights import (
    generate_heuristic_insights,
    generate_llm_insights,
)


ASSESSMENT = {
    "rows": 100,
    "columns": 2,
    "health_score": 70,
    "missing_cells": 10,
    "missing_percentage": 5.0,
    "duplicate_rows": 2,
    "dtype_issues": ["amount"],
    "highest_missing_columns": [("amount", 5.0)],
    "outlier_summary": {"amount": {"count": 3, "percent": 3.0}},
}


def test_heuristic_insights_are_generated():
    insights = generate_heuristic_insights(MagicMock(), ASSESSMENT)
    assert insights
    assert any("duplicate" in insight for insight in insights)


@patch.dict(os.environ, {"OPENAI_API_KEY": "test-key", "OPENAI_MODEL": "test-model"}, clear=False)
@patch("openai.OpenAI")
def test_llm_insights_are_parsed(mock_openai):
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"insights": ["Remove duplicate rows.", "Review amount outliers."]}'
                )
            )
        ]
    )

    insights = generate_llm_insights(MagicMock(), ASSESSMENT)

    assert insights == ["Remove duplicate rows.", "Review amount outliers."]
