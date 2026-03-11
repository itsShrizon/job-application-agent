import logging

from app.core.csv_manager import get_job_by_id, update_job
from app.core.parser import read_personal_md, read_job_circular
from app.core.llm_chains import invoke_cover_chain
from app.core.template_engine import fill_cover_template, compile_latex

logger = logging.getLogger(__name__)


def generate_cover(job_id: str) -> dict:
    job = get_job_by_id(job_id)
    profile = read_personal_md()

    profile_text = _format_profile(profile)

    content = invoke_cover_chain(
        profile=profile_text,
        company_name=job.get("company_name", ""),
        company_description=job.get("company_description", ""),
        job_title=job.get("title", ""),
        job_description=job.get("description_text", ""),
    )

    identity = {
        "name": profile.get("name", ""),
        "email": profile.get("email", ""),
        "phone": profile.get("phone", ""),
        "linkedin": profile.get("linkedin", ""),
        "github": profile.get("github", ""),
        "location": profile.get("location", ""),
        "portfolio": profile.get("portfolio", ""),
    }

    job_context = {
        "target_role": job.get("title", ""),
        "company_name": job.get("company_name", ""),
        "company_website": job.get("company_website", ""),
    }

    tex_path = fill_cover_template(identity, content, job_context)
    pdf_path = compile_latex(tex_path)

    update_job(job_id, {"cover_generated": "True"})

    logger.info(f"Cover letter generated for {job_id}: {pdf_path}")
    return {
        "pdf_path": str(pdf_path),
        "job_id": job_id,
        "job_title": job.get("title", ""),
        "company_name": job.get("company_name", ""),
    }


def generate_cover_from_file(file_path: str) -> dict:
    circular_text = read_job_circular(file_path)
    profile = read_personal_md()

    profile_text = _format_profile(profile)

    parts = file_path.replace(".md", "").split("_")
    company_name = parts[0] if parts else "Unknown"
    job_title = " ".join(parts[2:]) if len(parts) > 2 else "Role"

    content = invoke_cover_chain(
        profile=profile_text,
        company_name=company_name,
        company_description="",
        job_title=job_title,
        job_description=circular_text,
    )

    identity = {
        "name": profile.get("name", ""),
        "email": profile.get("email", ""),
        "phone": profile.get("phone", ""),
        "linkedin": profile.get("linkedin", ""),
        "github": profile.get("github", ""),
        "location": profile.get("location", ""),
        "portfolio": profile.get("portfolio", ""),
    }

    job_context = {
        "target_role": job_title,
        "company_name": company_name,
        "company_website": "",
    }

    tex_path = fill_cover_template(identity, content, job_context)
    pdf_path = compile_latex(tex_path)

    logger.info(f"Cover letter generated from file {file_path}: {pdf_path}")
    return {
        "pdf_path": str(pdf_path),
        "job_id": file_path,
        "job_title": job_title,
        "company_name": company_name,
    }


def _format_profile(profile: dict) -> str:
    parts = []
    for key in ["name", "email", "phone", "linkedin", "github", "location"]:
        if profile.get(key):
            parts.append(f"{key.title()}: {profile[key]}")
    if profile.get("skills"):
        parts.append(f"\nSkills:\n{profile['skills']}")
    if profile.get("experience"):
        parts.append(f"\nExperience:\n{profile['experience']}")
    return "\n".join(parts)
