from app.core.parser import parse_personal_md, _split_sections, _extract_field


def test_parse_personal_md_extracts_name():
    content = "# Personal Information\n**Name:** John Doe\n**Email:** john@test.com\n"
    result = parse_personal_md(content)
    assert result["name"] == "John Doe"
    assert result["email"] == "john@test.com"


def test_parse_personal_md_extracts_skills():
    content = "# Personal Information\n**Name:** Test\n\n# Skills\nPython, JS\n"
    result = parse_personal_md(content)
    assert "Python" in result["skills"]


def test_split_sections():
    content = "# Section A\nContent A\n# Section B\nContent B\n"
    sections = _split_sections(content)
    assert "section a" in sections
    assert "section b" in sections
    assert "Content A" in sections["section a"]


def test_extract_field():
    text = "**Name:** Jane Smith\n**Email:** jane@test.com"
    assert _extract_field(text, "name") == "Jane Smith"
    assert _extract_field(text, "email") == "jane@test.com"
    assert _extract_field(text, "phone") == ""


def test_parse_personal_md_missing_fields():
    content = "# Personal Information\n**Name:** Test\n"
    result = parse_personal_md(content)
    assert result["name"] == "Test"
    assert result["phone"] == ""
    assert result["skills"] == ""
