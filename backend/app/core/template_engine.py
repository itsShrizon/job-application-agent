import re
import shutil
import subprocess
import logging
import platform
from pathlib import Path
from datetime import date

from app.core.config import settings

logger = logging.getLogger(__name__)

# Resolve pdflatex binary — try PATH first, then common MiKTeX install on Windows
def _find_pdflatex() -> str:
    if shutil.which("pdflatex"):
        return "pdflatex"
    if platform.system() == "Windows":
        candidate = Path(r"C:\Users\Codixel_\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe")
        if candidate.exists():
            return str(candidate)
    raise FileNotFoundError(
        "pdflatex not found. Install MiKTeX from https://miktex.org/download "
        "or add it to your PATH."
    )

PDFLATEX = _find_pdflatex()

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

    # 1. Temporarily replace valid LaTeX commands we want to KEEP with a safe placeholder
    # By placing inner elements (\href) before outer wrappers (\textbf), we support nesting.
    safe_patterns = [
        r"\\\\",                                                # Line breaks
        r"\\href{[^}]+}{[^}]+}",                                # Links (most nested)
        r"\\textbf{[^}]+}",                                     # Bolds (can contain protected blocks)
        r"\\textit{[^}]+}",                                     # Italics
        r"\\begin{[^}]+}(?:\[[^\]]+\])?",                       # Begin blocks with optional args
        r"\\end{[^}]+}",                                        # End blocks
        r"\\item\s?",                                           # Items
        r"\\vspace{[^}]+}",                                     # Spacing
        r"\\hfill",                                             # Fill
    ]

    protected_blocks = []
    
    def shield_match(match):
        idx = len(protected_blocks)
        protected_blocks.append(match.group(0))
        return f"LATEXSAFEBLOCK{idx}"

    protected_text = text
    for pattern in safe_patterns:
        protected_text = re.sub(pattern, shield_match, protected_text)

    # 2. Escape the remaining plain text normally
    escaped = protected_text
    escaped = escaped.replace("\\", LATEX_SPECIAL["\\"])
    for char, replacement in LATEX_SPECIAL.items():
        if char == "\\":
            continue
        escaped = escaped.replace(char, replacement)

    # 3. Restore the protected blocks inside-out (backwards)
    for idx, block in reversed(list(enumerate(protected_blocks))):
        escaped = escaped.replace(f"LATEXSAFEBLOCK{idx}", block)

    return escaped


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
        "{{ACHIEVEMENTS}}": escape_latex(content.get("achievements", "")),
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
    job_id = _sanitize_filename(job_context.get("job_id", ""))
    
    if job_id:
        filename = f"{company}_{role}_{job_id}_{today}"
    else:
        filename = f"{company}_{role}_{today}"

    # Downgrade em/en dashes before stripping non-ASCII characters
    tex = tex.replace("—", "-").replace("–", "-")
    import unicodedata
    tex = unicodedata.normalize('NFKD', tex).encode('ascii', 'ignore').decode('ascii')

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
    job_id = _sanitize_filename(job_context.get("job_id", ""))

    if job_id:
        filename = f"{company}_{role}_{job_id}_{today}"
    else:
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
            [PDFLATEX, "-interaction=nonstopmode", "-output-directory", str(output_dir), str(tex_path)],
            capture_output=True,
            text=True,
            timeout=120,
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
