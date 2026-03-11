import json
import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.config import settings

logger = logging.getLogger(__name__)

CV_SYSTEM_PROMPT = r"""You are an expert ATS resume optimizer. Given a candidate's profile, GitHub projects, and a target job description, generate tailored CV content.

Rules:
- Prioritize keywords from the job description (e.g., "Machine Learning", "Python", "Cloud Run", "REST API").
- Rewrite bullet points to be highly technical and relevant to the target role.
- When choosing projects, select them based on: 1. Technology stack match with the target job (MOST IMPORTANT). 2. High number of commits. 3. Large codebase size (KB).
- Use strong action verbs (Architected, Engineered, Optimized, Deployed).
- Quantify achievements with metrics (e.g., "increased accuracy by 10%", "reduced latency by 200ms").
- Select the optimal number of projects to dynamically fill exactly one page (filling it to the brim without overflowing). Consider the length of the previous sections.
- CRITICAL: AVOID using special LaTeX characters like ^, ~, $, or % in plain text. Use plain text like "SIU S12" or "10 percent". Replace explicit "&" with "and" or escape as "\&".
- REWRITE project names to be highly technical and academic. Avoid generic terms.
  * Good: "Hierarchical Transformer-Based Semantic Segmentation for Medical Imagery"
  * Bad: "Medical QA Pipeline" or "Dips Framework"
- For [PROJECTS], provide 2-3 detailed bullet points per project. Mention specific frameworks and the technical challenge solved.
- YOU MUST populate [ACHIEVEMENTS] using the candidate's actual achievements (e.g., Dean's List, Scholarships) found in the profile.

Output format — return EXACTLY these sections with these headers. YOU MUST USE VALID LATEX FORMATTING:

[SUMMARY]
A 2-3 sentence technical professional summary (plain text).

[SKILLS]
\begin{{itemize}}
    \item \textbf{{Frameworks \& Languages:}} Python, PyTorch, TensorFlow, GCP, SQL, etc.
    \item \textbf{{Specializations:}} LLM Fine-tuning, RAG, NLP, CV, etc.
\end{{itemize}}

[EXPERIENCE]
For each role:
\begin{{itemize}}
    \item \textbf{{COMPANY_NAME}} \hfill DATES \\
    \textbf{{JOB_TITLE}} \\
    - Developed technical solution X using Y resulting in Z. \\
    - Optimized performance by A percent via B implementation.
\end{{itemize}}

[PROJECTS]
Select the optimal number of projects to fill the single page perfectly. Format EXACTLY like this:
\begin{{itemize}}
    \item \textbf{{\href{{URL_IF_AVAILABLE}}{{TECHNICAL_ACADEMIC_PROJECT_NAME}}}} \\
    - Built a technical solution for X using Y (e.g., PyTorch, FastAPI). \\
    - Achieved performance metric Z through algorithmic optimization W.
\end{{itemize}}

[EDUCATION]
For each entry:
\textbf{{INSTITUTION}} \hfill DATES \\
\textit{{DEGREE}} \hfill \textbf{{Details (e.g., CGPA 3.80 / 4.00)}} \\

[ACHIEVEMENTS]
\begin{{itemize}}
    \item \textbf{{ACHIEVEMENT_NAME}}, \textit{{ISSUER}} \hfill DATE
\end{{itemize}}

[CERTIFICATIONS]
\begin{{itemize}}
    \item \textbf{{CERTIFICATION_NAME}}, \textit{{ISSUER}} \hfill DATE
\end{{itemize}}"""

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

SCORING_SYSTEM_PROMPT = """You are a highly analytical, strict job relevance scoring engine. Your task is to mathematically score each job for the candidate on a strict scale of 0.0 to 100.0.

CRITICAL RULES:
1. MAX SCORE is 100.0. MIN SCORE is 0.0. Do NOT exceed 100 under ANY circumstances (e.g., no 500 or 1500).
2. Do NOT append a '%' sign to the score. Output ONLY a pure float number (e.g., 85.5, 42.0).
3. BE RUTHLESS AND DETERMINISTIC. Start at 100 and strictly DEDUCT points:
   - Skills match (Max 40 pts): Deduct 5-10 pts for every missing core skill or unaligned tech stack.
   - Experience level (Max 25 pts): Deduct 15-25 pts if candidate is Junior but job is Senior/Lead, or vice versa.
   - Domain fit (Max 15 pts): Deduct 5-15 pts if the industry completely shifts (e.g., Healthcare to Crypto).
   - Location (Max 10 pts): Deduct 10 pts if timezone or physical location differs severely from candidate preference.
   - Role alignment (Max 10 pts): Deduct 5-10 pts if the job title does not immediately reflect the candidate's career goals.
4. UNIQUENESS IS MANDATORY. You MUST differentiate the scores across the batch based on nuanced deductions. Do NOT assign the exact same score (like 100.0 or 0.0) to multiple jobs unless they are absolute clones. If a job is an 80 and one is slightly better, give the other an 82.5.

Output format MUST be a pure JSON array of objects with keys: `job_index` (integer, 0-based), `score` (float between 0.0 and 100.0), and `reason` (1 sentence explaining specific deductions). ONLY return valid JSON."""

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
        "achievements": sections.get("achievements", ""),
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


CV_EDIT_SYSTEM_PROMPT = r"""You are a LaTeX CV editor. The user will give you instructions to modify their CV.

Rules:
- Return ONLY the complete modified LaTeX source code, nothing else
- Do NOT wrap in markdown fences or add any explanation
- Preserve all LaTeX formatting, packages, and document structure
- Keep the CV fitting on exactly 1 page
- AVOID using special LaTeX characters like ^, ~, $, or % in plain text unless they are escaped"""

CV_EDIT_USER_PROMPT = """Current CV LaTeX:
{latex}

Instruction: {instruction}

Return the complete modified LaTeX source."""


def invoke_cv_edit_chain(latex: str, instruction: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", CV_EDIT_SYSTEM_PROMPT),
        ("human", CV_EDIT_USER_PROMPT),
    ])
    chain = prompt | _cv_llm() | StrOutputParser()
    return chain.invoke({"latex": latex, "instruction": instruction})


def _parse_scoring_response(raw: str) -> list[dict]:
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```") and not l.strip().startswith("json")]
        cleaned = "\n".join(lines)

    try:
        results = json.loads(cleaned)
        if isinstance(results, list):
            valid_results = []
            for item in results:
                if not isinstance(item, dict):
                    continue
                score_raw = item.get("score", 0.0)
                try:
                    score_str = str(score_raw).replace("%", "").strip()
                    score_val = float(score_str)
                    
                    if score_val > 100.0:
                        score_val = 100.0
                    elif score_val < 0.0:
                        score_val = 0.0
                        
                    item["score"] = score_val
                    valid_results.append(item)
                except (ValueError, TypeError):
                    item["score"] = 0.0
                    valid_results.append(item)
            return valid_results
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse scoring response: {cleaned[:200]}")

    return []
