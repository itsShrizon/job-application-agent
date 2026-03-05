import re
import subprocess
import logging
from pathlib import Path
from datetime import date

from app.core.config import settings

logger = logging.getLogger(__name__)

TEMPLATE_MAP = {
    "t1": "cv_template_1.tex",
    "t2": "cv_template_2.tex",
    "t3": "cv_template_3.tex",
}

LATEX_SPECIAL = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}


def escape_latex(text: str) -> str:
    if not text:
        return ""
    result = text
    result = result.replace("\\", LATEX_SPECIAL["\\"])
    for char, replacement in LATEX_SPECIAL.items():
        if char == "\\":
            continue
        result = result.replace(char, replacement)
    return result


def fill_cv_template(template: str, identity: dict, content: dict, job_context: dict) -> Path:
    template_file = TEMPLATE_MAP.get(template)
    if not template_file:
        raise ValueError(f"Unknown template: {template}. Use t1, t2, or t3.")

    template_path = settings.templates_path / "cv" / template_file
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    tex = template_path.read_text(encoding="utf-8")

    replacements = {
        "{{NAME}}": escape_latex(identity.get("name", "")),
        "{{EMAIL}}": escape_latex(identity.get("email", "")),
        "{{PHONE}}": escape_latex(identity.get("phone", "")),
        "{{LINKEDIN}}": escape_latex(identity.get("linkedin", "")),
        "{{GITHUB}}": escape_latex(identity.get("github", "")),
        "{{LOCATION}}": escape_latex(identity.get("location", "")),
        "{{PORTFOLIO}}": escape_latex(identity.get("portfolio", "")),
        "{{SUMMARY}}": escape_latex(content.get("summary", "")),
        "{{SKILLS}}": escape_latex(content.get("skills", "")),
        "{{EXPERIENCE}}": escape_latex(content.get("experience", "")),
        "{{PROJECTS}}": escape_latex(content.get("projects", "")),
        "{{EDUCATION}}": escape_latex(content.get("education", "")),
        "{{CERTIFICATIONS}}": escape_latex(content.get("certifications", "")),
        "{{TARGET_ROLE}}": escape_latex(job_context.get("target_role", "")),
        "{{COMPANY_NAME}}": escape_latex(job_context.get("company_name", "")),
        "{{COMPANY_WEBSITE}}": escape_latex(job_context.get("company_website", "")),
    }

    for placeholder, value in replacements.items():
        tex = tex.replace(placeholder, value)

    remaining = re.findall(r"\{\{[A-Z_]+\}\}", tex)
    if remaining:
        raise ValueError(f"Unreplaced template variables: {remaining}")

    company = _sanitize_filename(job_context.get("company_name", "Unknown"))
    role = _sanitize_filename(job_context.get("target_role", "Role"))
    today = date.today().strftime("%Y_%m_%d")
    filename = f"{company}_{role}_{today}"

    output_dir = settings.output_path / "cv"
    output_dir.mkdir(parents=True, exist_ok=True)

    tex_path = output_dir / f"{filename}.tex"
    tex_path.write_text(tex, encoding="utf-8")

    return tex_path


def fill_cover_template(identity: dict, content: dict, job_context: dict) -> Path:
    template_path = settings.templates_path / "cover" / "cover_template_1.tex"
    if not template_path.exists():
        raise FileNotFoundError(f"Cover template not found: {template_path}")

    tex = template_path.read_text(encoding="utf-8")

    replacements = {
        "{{NAME}}": escape_latex(identity.get("name", "")),
        "{{EMAIL}}": escape_latex(identity.get("email", "")),
        "{{PHONE}}": escape_latex(identity.get("phone", "")),
        "{{LINKEDIN}}": escape_latex(identity.get("linkedin", "")),
        "{{GITHUB}}": escape_latex(identity.get("github", "")),
        "{{LOCATION}}": escape_latex(identity.get("location", "")),
        "{{PORTFOLIO}}": escape_latex(identity.get("portfolio", "")),
        "{{COVER_DATE}}": escape_latex(date.today().strftime("%B %d, %Y")),
        "{{COVER_SALUTATION}}": escape_latex(content.get("salutation", "Dear Hiring Manager,")),
        "{{COVER_BODY}}": escape_latex(content.get("body", "")),
        "{{COVER_CLOSING}}": escape_latex(content.get("closing", "Sincerely,")),
        "{{TARGET_ROLE}}": escape_latex(job_context.get("target_role", "")),
        "{{COMPANY_NAME}}": escape_latex(job_context.get("company_name", "")),
        "{{COMPANY_WEBSITE}}": escape_latex(job_context.get("company_website", "")),
    }

    for placeholder, value in replacements.items():
        tex = tex.replace(placeholder, value)

    remaining = re.findall(r"\{\{[A-Z_]+\}\}", tex)
    if remaining:
        raise ValueError(f"Unreplaced template variables: {remaining}")

    company = _sanitize_filename(job_context.get("company_name", "Unknown"))
    role = _sanitize_filename(job_context.get("target_role", "Role"))
    today = date.today().strftime("%Y_%m_%d")
    filename = f"{company}_{role}_{today}"

    output_dir = settings.output_path / "cover"
    output_dir.mkdir(parents=True, exist_ok=True)

    tex_path = output_dir / f"{filename}.tex"
    tex_path.write_text(tex, encoding="utf-8")

    return tex_path


def compile_latex(tex_path: Path) -> Path:
    output_dir = tex_path.parent
    pdf_path = tex_path.with_suffix(".pdf")

    for pass_num in range(2):
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-output-directory", str(output_dir), str(tex_path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0 and pass_num == 1:
            logger.error(f"LaTeX compilation failed:\n{result.stdout}\n{result.stderr}")
            raise RuntimeError(f"LaTeX compilation failed. Check {tex_path} for errors.\n{result.stdout[-500:]}")

    if not pdf_path.exists():
        raise RuntimeError(f"PDF not generated at {pdf_path}")

    for ext in [".aux", ".log", ".out"]:
        cleanup = tex_path.with_suffix(ext)
        if cleanup.exists():
            cleanup.unlink()

    logger.info(f"Compiled: {pdf_path}")
    return pdf_path


def _sanitize_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "", name.replace(" ", ""))
