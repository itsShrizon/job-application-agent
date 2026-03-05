from unittest.mock import patch
from pathlib import Path


@patch("app.services.cover_service.update_job")
@patch("app.services.cover_service.compile_latex")
@patch("app.services.cover_service.fill_cover_template")
@patch("app.services.cover_service.invoke_cover_chain")
@patch("app.services.cover_service.read_personal_md")
@patch("app.services.cover_service.get_job_by_id")
def test_generate_cover(mock_job, mock_profile, mock_chain, mock_fill, mock_compile, mock_update):
    mock_job.return_value = {
        "title": "Data Analyst",
        "company_name": "DataCo",
        "company_website": "https://dataco.com",
        "company_description": "We analyze data",
        "description_text": "Analyze things",
    }
    mock_profile.return_value = {
        "name": "Test", "email": "t@t.com", "phone": "",
        "linkedin": "", "github": "", "location": "", "portfolio": "",
        "skills": "SQL", "experience": "2y", "education": "BSc",
    }
    mock_chain.return_value = {
        "salutation": "Dear Hiring Manager,",
        "body": "I am writing to apply...",
        "closing": "Sincerely,",
    }
    mock_fill.return_value = Path("/tmp/cover.tex")
    mock_compile.return_value = Path("/tmp/cover.pdf")

    from app.services.cover_service import generate_cover
    result = generate_cover("DEF456")

    assert result["job_title"] == "Data Analyst"
    assert result["company_name"] == "DataCo"
    mock_update.assert_called_once()
