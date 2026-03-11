from unittest.mock import patch, MagicMock
from pathlib import Path


@patch("app.services.cv_service.update_job")
@patch("app.services.cv_service.compile_latex")
@patch("app.services.cv_service.fill_cv_template")
@patch("app.services.cv_service.invoke_cv_chain")
@patch("app.services.cv_service.read_github_md")
@patch("app.services.cv_service.read_personal_md")
@patch("app.services.cv_service.get_job_by_id")
def test_generate_cv(mock_job, mock_profile, mock_github, mock_chain, mock_fill, mock_compile, mock_update):
    mock_job.return_value = {
        "title": "Software Engineer",
        "company_name": "TechCorp",
        "company_website": "https://techcorp.com",
        "description_text": "Build great software",
    }
    mock_profile.return_value = {
        "name": "Test User", "email": "test@test.com", "phone": "",
        "linkedin": "", "github": "", "location": "", "portfolio": "",
        "skills": "Python", "experience": "3 years", "education": "BSc",
        "certifications": "",
    }
    mock_github.return_value = "# Projects"
    mock_chain.return_value = {
        "summary": "Experienced dev", "skills": "Python",
        "experience": "3y SWE", "projects": "P1",
        "education": "BSc", "certifications": "",
    }
    mock_fill.return_value = Path("/tmp/test.tex")
    mock_compile.return_value = Path("/tmp/test.pdf")

    from app.services.cv_service import generate_cv
    result = generate_cv("ABC123", "t1")

    assert result["job_title"] == "Software Engineer"
    assert result["company_name"] == "TechCorp"
    assert result["template_used"] == "t1"
    mock_update.assert_called_once()
