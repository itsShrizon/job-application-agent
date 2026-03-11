from app.core.llm_chains import _parse_cv_sections, _parse_cover_sections, _parse_scoring_response


def test_parse_cv_sections():
    raw = """[SUMMARY]
Experienced engineer.

[SKILLS]
Python, JS, SQL

[EXPERIENCE]
SWE | Corp | 2022-2024
- Built APIs

[PROJECTS]
MyApp | Python
- Did stuff

[EDUCATION]
BSc | University | 2018-2022

[CERTIFICATIONS]
AWS SA | Amazon | 2024"""

    result = _parse_cv_sections(raw)
    assert "engineer" in result["summary"].lower()
    assert "Python" in result["skills"]
    assert "Corp" in result["experience"]
    assert "MyApp" in result["projects"]


def test_parse_cover_sections():
    raw = """[SALUTATION]
Dear Hiring Manager,

[BODY]
I am writing to express my interest.

[CLOSING]
Sincerely,"""

    result = _parse_cover_sections(raw)
    assert "Dear" in result["salutation"]
    assert "interest" in result["body"]
    assert "Sincerely" in result["closing"]


def test_parse_scoring_response():
    raw = '[{"job_index": 0, "score": 85.0, "reason": "Good match"}]'
    result = _parse_scoring_response(raw)
    assert len(result) == 1
    assert result[0]["score"] == 85.0


def test_parse_scoring_response_with_code_fence():
    raw = '```json\n[{"job_index": 0, "score": 70.0, "reason": "OK"}]\n```'
    result = _parse_scoring_response(raw)
    assert len(result) == 1


def test_parse_scoring_response_invalid():
    result = _parse_scoring_response("not json")
    assert result == []
