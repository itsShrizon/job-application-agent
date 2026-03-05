from unittest.mock import patch, MagicMock

import pandas as pd

from app.services.scoring_service import score_all_unscored, get_top_jobs


@patch("app.services.scoring_service.get_scored_jobs")
@patch("app.services.scoring_service.save_jobs")
@patch("app.services.scoring_service.load_jobs")
@patch("app.services.scoring_service.invoke_scoring_chain")
@patch("app.services.scoring_service.get_unscored_jobs")
@patch("app.services.scoring_service.read_personal_md")
def test_score_all_unscored_empty(mock_profile, mock_unscored, mock_chain, mock_load, mock_save, mock_top):
    mock_profile.return_value = {"name": "Test", "skills": "Python"}
    mock_unscored.return_value = pd.DataFrame()
    mock_top.return_value = pd.DataFrame()

    result = score_all_unscored()
    assert result["scored_count"] == 0
    mock_chain.assert_not_called()


@patch("app.services.scoring_service.get_scored_jobs")
def test_get_top_jobs(mock_scored):
    mock_scored.return_value = pd.DataFrame([
        {"job_id": "A", "title": "Dev", "relevance_score": "90"},
    ])

    result = get_top_jobs(limit=5)
    assert len(result) == 1
