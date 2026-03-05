import json
import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.config import settings

logger = logging.getLogger(__name__)

CV_SYSTEM_PROMPT = """You are an expert ATS resume optimizer. Given a candidate's profile, GitHub projects, and a target job description, generate tailored CV content.

Rules:
- Prioritize keywords from the job description
- Rewrite bullet points to be relevant to the target role
- Select the most relevant projects from GitHub
- Use strong action verbs (designed, implemented, optimized, deployed, etc.)
- NEVER fabricate experience, skills, or achievements
- Quantify achievements where possible
- Keep content concise and impactful
- Select AT MOST 4 projects for the [PROJECTS] section — pick the ones most relevant to the target role, ranked by relevance

Output format — return EXACTLY these sections with these headers:

[SUMMARY]
A 2-3 sentence professional summary tailored to the role.

[SKILLS]
Comma-separated list of relevant skills, prioritizing those mentioned in the job description.

[EXPERIENCE]
Each experience entry as:
TITLE | COMPANY | DATES
- Bullet point 1
- Bullet point 2
- Bullet point 3

[PROJECTS]
Each project entry as:
PROJECT_NAME | TECHNOLOGIES
- Description bullet 1
- Description bullet 2

[EDUCATION]
Each entry as:
DEGREE | INSTITUTION | DATES
- Detail (if any)

[CERTIFICATIONS]
Each as: CERTIFICATION_NAME | ISSUER | DATE"""

CV_USER_PROMPT = """Candidate Profile:
{profile}

GitHub Projects:
{github}

Target Job:
Company: {company_name}
Role: {job_title}
Description:
{job_description}

Generate tailored CV content for this role."""

COVER_SYSTEM_PROMPT = """You are an expert cover letter writer. Generate a tailored cover letter.

Rules:
- Open with genuine interest in the company (use company description provided)
- Connect candidate's experience directly to job requirements
- Highlight 2-3 specific achievements relevant to the role
- Keep it 250-350 words
- Professional but authentic tone
- NEVER fabricate

Output format — return EXACTLY these sections:

[SALUTATION]
The greeting line (e.g., "Dear Hiring Manager,")

[BODY]
The full cover letter body (3-4 paragraphs).

[CLOSING]
The sign-off (e.g., "Sincerely,")"""

COVER_USER_PROMPT = """Candidate Profile:
{profile}

Target Job:
Company: {company_name}
Company Description: {company_description}
Role: {job_title}
Description:
{job_description}

Generate a tailored cover letter."""

SCORING_SYSTEM_PROMPT = """You are a job relevance scoring system. Score each job for the candidate on a scale of 0.0 to 100.0.

Scoring criteria:
- Skills match (40%): How well do the candidate's skills match the job requirements?
- Experience level (25%): Does the candidate's experience level align?
- Domain fit (15%): Is the candidate's domain/industry experience relevant?
- Location (10%): Does the location match the candidate's preference?
- Role alignment (10%): How closely does the job title match what the candidate is looking for?

For each job, return a JSON object with: job_index (0-based), score (0.0-100.0), reason (1 sentence).

Return a JSON array of these objects. ONLY return valid JSON, no other text."""

SCORING_USER_PROMPT = """Candidate Summary:
{candidate_summary}

Jobs to score:
{jobs_batch}

Return a JSON array of scoring results."""


def _cv_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.OPENAI_CV_MODEL,
        temperature=settings.OPENAI_CV_TEMPERATURE,
        max_tokens=settings.OPENAI_MAX_TOKENS,
        api_key=settings.OPENAI_API_KEY,
    )


def _scoring_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.OPENAI_SCORING_MODEL,
        temperature=settings.OPENAI_SCORING_TEMPERATURE,
        max_tokens=settings.OPENAI_MAX_TOKENS,
        api_key=settings.OPENAI_API_KEY,
    )


def _cover_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.OPENAI_CV_MODEL,
        temperature=settings.OPENAI_COVER_TEMPERATURE,
        max_tokens=settings.OPENAI_MAX_TOKENS,
        api_key=settings.OPENAI_API_KEY,
    )


def invoke_cv_chain(profile: str, github: str, company_name: str, job_title: str, job_description: str) -> dict:
    prompt = ChatPromptTemplate.from_messages([
        ("system", CV_SYSTEM_PROMPT),
        ("human", CV_USER_PROMPT),
    ])
    chain = prompt | _cv_llm() | StrOutputParser()

    raw = chain.invoke({
        "profile": profile,
        "github": github,
        "company_name": company_name,
        "job_title": job_title,
        "job_description": job_description,
    })

    return _parse_cv_sections(raw)


def invoke_cover_chain(profile: str, company_name: str, company_description: str, job_title: str, job_description: str) -> dict:
    prompt = ChatPromptTemplate.from_messages([
        ("system", COVER_SYSTEM_PROMPT),
        ("human", COVER_USER_PROMPT),
    ])
    chain = prompt | _cover_llm() | StrOutputParser()

    raw = chain.invoke({
        "profile": profile,
        "company_name": company_name,
        "company_description": company_description,
        "job_title": job_title,
        "job_description": job_description,
    })

    return _parse_cover_sections(raw)


def invoke_scoring_chain(candidate_summary: str, jobs_batch: str) -> list[dict]:
    prompt = ChatPromptTemplate.from_messages([
        ("system", SCORING_SYSTEM_PROMPT),
        ("human", SCORING_USER_PROMPT),
    ])
    chain = prompt | _scoring_llm() | StrOutputParser()

    raw = chain.invoke({
        "candidate_summary": candidate_summary,
        "jobs_batch": jobs_batch,
    })

    return _parse_scoring_response(raw)


def _parse_cv_sections(raw: str) -> dict:
    sections = {}
    current_key = None
    current_lines = []

    for line in raw.split("\n"):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if current_key:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = stripped[1:-1].lower()
            current_lines = []
        else:
            current_lines.append(line)

    if current_key:
        sections[current_key] = "\n".join(current_lines).strip()

    return {
        "summary": sections.get("summary", ""),
        "skills": sections.get("skills", ""),
        "experience": sections.get("experience", ""),
        "projects": sections.get("projects", ""),
        "education": sections.get("education", ""),
        "certifications": sections.get("certifications", ""),
    }


def _parse_cover_sections(raw: str) -> dict:
    sections = {}
    current_key = None
    current_lines = []

    for line in raw.split("\n"):
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if current_key:
                sections[current_key] = "\n".join(current_lines).strip()
            current_key = stripped[1:-1].lower()
            current_lines = []
        else:
            current_lines.append(line)

    if current_key:
        sections[current_key] = "\n".join(current_lines).strip()

    return {
        "salutation": sections.get("salutation", "Dear Hiring Manager,"),
        "body": sections.get("body", ""),
        "closing": sections.get("closing", "Sincerely,"),
    }


def _parse_scoring_response(raw: str) -> list[dict]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(lines)

    try:
        results = json.loads(cleaned)
        if isinstance(results, list):
            return results
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse scoring response: {cleaned[:200]}")

    return []
