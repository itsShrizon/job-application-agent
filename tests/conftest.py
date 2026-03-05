import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def tmp_data_dir(tmp_path):
    (tmp_path / "scrape_state").mkdir()
    return tmp_path


@pytest.fixture
def sample_personal_md(tmp_data_dir):
    content = """# Personal Information
**Name:** Tanzir Hossain
**Email:** tanzir@example.com
**Phone:** +8801234567890
**LinkedIn:** https://linkedin.com/in/tanzir
**GitHub:** https://github.com/tanzir
**Location:** Dhaka, Bangladesh
**Portfolio:** https://tanzir.dev

# Summary
Experienced software engineer with expertise in Python, machine learning, and web development.

# Skills
Python, JavaScript, TypeScript, React, FastAPI, Django, PostgreSQL, Docker, AWS, Machine Learning, NLP, Git

# Experience
## Software Engineer | TechCorp | 2024–Present
- Developed REST APIs serving 10K+ daily requests
- Built ML pipeline reducing processing time by 40%
- Led migration from monolith to microservices

## Junior Developer | StartupXYZ | 2022–2024
- Built React dashboard for analytics
- Implemented CI/CD pipeline with GitHub Actions

# Education
## BSc Computer Science | BUET | 2018–2022
- CGPA: 3.8/4.0
- Thesis: NLP-based document classification

# Certifications
AWS Solutions Architect Associate | 2024
Google Professional Data Engineer | 2023
"""
    path = tmp_data_dir / "personal.md"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def mock_settings(tmp_data_dir, tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "cv").mkdir()
    (output_dir / "cover").mkdir()

    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    (templates_dir / "cv").mkdir()
    (templates_dir / "cover").mkdir()

    with patch("app.core.config.settings") as mock:
        mock.data_path = tmp_data_dir
        mock.output_path = output_dir
        mock.templates_path = templates_dir
        mock.logs_path = tmp_path / "logs"
        mock.DEFAULT_DEADLINE_DAYS = 30
        mock.OPENAI_API_KEY = "test-key"
        mock.OPENAI_CV_MODEL = "gpt-4o"
        mock.OPENAI_SCORING_MODEL = "gpt-4.1-nano"
        mock.OPENAI_MAX_TOKENS = 4000
        mock.OPENAI_CV_TEMPERATURE = 0.3
        mock.OPENAI_SCORING_TEMPERATURE = 0.1
        mock.OPENAI_COVER_TEMPERATURE = 0.4
        mock.GITHUB_PAT_TOKEN = "test-token"
        mock.GITHUB_USERNAME = "testuser"
        mock.APIFY_API_TOKEN = "test-apify"
        yield mock


@pytest.fixture
def test_client():
    from app.main import app
    return TestClient(app)
