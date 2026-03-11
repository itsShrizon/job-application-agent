from unittest.mock import patch, MagicMock


@patch("app.services.github_service.settings")
@patch("app.services.github_service.requests.get")
def test_refresh_github(mock_get, mock_settings, tmp_path):
    mock_settings.GITHUB_USERNAME = "testuser"
    mock_settings.GITHUB_PAT_TOKEN = "tok"
    mock_settings.data_path = tmp_path

    mock_resp = MagicMock()
    mock_resp.json.return_value = [
        {
            "name": "project1",
            "description": "A cool project",
            "language": "Python",
            "html_url": "https://github.com/testuser/project1",
            "stargazers_count": 5,
            "fork": False,
            "topics": ["python", "ml"],
        },
    ]
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    from app.services.github_service import refresh_github
    result = refresh_github()

    assert result["repo_count"] == 1
    assert (tmp_path / "github.md").exists()
