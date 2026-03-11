import re
from pathlib import Path

from app.core.config import settings


def read_personal_md() -> dict:
    path = settings.data_path / "personal.md"
    if not path.exists():
        raise FileNotFoundError("personal.md not found in data/ directory.")
    return parse_personal_md(path.read_text(encoding="utf-8"))


def parse_personal_md(content: str) -> dict:
    sections = _split_sections(content)
    profile = {}

    personal = sections.get("personal information", "")
    profile["name"] = _extract_field(personal, "name")
    profile["email"] = _extract_field(personal, "email")
    profile["phone"] = _extract_field(personal, "phone")
    profile["linkedin"] = _extract_field(personal, "linkedin")
    profile["github"] = _extract_field(personal, "github")
    profile["location"] = _extract_field(personal, "location")
    profile["portfolio"] = _extract_field(personal, "portfolio")

    profile["skills"] = sections.get("skills", "").strip()
    profile["experience"] = sections.get("experience", "").strip()
    profile["education"] = sections.get("education", "").strip()
    profile["certifications"] = sections.get("certifications", "").strip()
    profile["summary"] = sections.get("summary", "").strip()
    profile["achievements"] = sections.get("achievements", "").strip()

    return profile


def validate_personal_md() -> dict:
    errors = []
    try:
        profile = read_personal_md()
    except FileNotFoundError as e:
        return {"valid": False, "errors": [str(e)]}

    required_sections = {
        "name": "Name is missing",
        "skills": "No skills found",
        "experience": "No experience found",
        "education": "No education found",
    }
    for field, msg in required_sections.items():
        if not profile.get(field):
            errors.append(f"ERROR: {msg}")

    email = profile.get("email", "")
    if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        errors.append("WARNING: Invalid email format")

    return {"valid": len(errors) == 0, "errors": errors}


def read_github_md() -> str:
    path = settings.data_path / "github.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def read_job_circular(filename: str) -> str:
    path = Path(settings.data_path).parent / "job_circular" / filename
    if not path.exists():
        raise FileNotFoundError(f"Job circular not found: {filename}")
    return path.read_text(encoding="utf-8")


def _split_sections(content: str) -> dict:
    sections = {}
    current_key = None
    current_lines = []

    for line in content.split("\n"):
        header_match = re.match(r"^#{1,3}\s+(.+)$", line)
        if header_match:
            if current_key is not None:
                sections[current_key] = "\n".join(current_lines)
            current_key = header_match.group(1).strip().lower()
            current_lines = []
        else:
            current_lines.append(line)

    if current_key is not None:
        sections[current_key] = "\n".join(current_lines)

    return sections


def _extract_field(text: str, field_name: str) -> str:
    pattern = rf"(?i)\*{{0,2}}{field_name}\s*[:：]\s*\*{{0,2}}\s*(.+)"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""
