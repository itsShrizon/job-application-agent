from app.core.template_engine import escape_latex, _sanitize_filename


def test_escape_latex_special_chars():
    assert escape_latex("R&D") == r"R\&D"
    assert escape_latex("100%") == r"100\%"
    assert escape_latex("$100") == r"\$100"
    assert escape_latex("#1") == r"\#1"
    assert escape_latex("role_name") == r"role\_name"


def test_escape_latex_empty():
    assert escape_latex("") == ""
    assert escape_latex(None) == ""


def test_escape_latex_no_special():
    assert escape_latex("Hello World") == "Hello World"


def test_sanitize_filename():
    assert _sanitize_filename("Facebook Inc.") == "FacebookInc"
    assert _sanitize_filename("BRAC IT") == "BRACIT"
    assert _sanitize_filename("test@123") == "test123"
