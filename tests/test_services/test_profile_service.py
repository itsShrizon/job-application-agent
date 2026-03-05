from unittest.mock import patch


@patch("app.services.profile_service.read_personal_md")
def test_get_profile(mock_read):
    mock_read.return_value = {"name": "Test", "email": "t@t.com", "skills": "Python"}

    from app.services.profile_service import get_profile
    result = get_profile()
    assert result["name"] == "Test"


@patch("app.services.profile_service.validate_personal_md")
def test_validate_profile(mock_validate):
    mock_validate.return_value = {"valid": True, "errors": []}

    from app.services.profile_service import validate_profile
    result = validate_profile()
    assert result["valid"] is True
