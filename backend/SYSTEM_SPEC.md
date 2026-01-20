# Coding Agent for CV Generation & Job Tracking

**Author:** Tanzir Hossain
**Version:** 4.0
**Date:** 2026
**Status:** Draft

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-01 | Tanzir Hossain | Initial specification |
| 2.0 | 2026-03-05 | Tanzir Hossain | Expanded with schemas, error handling, validation, prompt strategy, testing, logging |
| 3.0 | 2026-03-05 | Tanzir Hossain | Added LinkedIn scraping (Apify), job scoring (GPT-4.1-nano), CSV database, cover letters, LangChain |
| 4.0 | 2026-03-05 | Tanzir Hossain | Restructured to FastAPI service-layer architecture. CLI is now a thin client. API-first design for future frontend. Pydantic schemas, background tasks, proper Python packaging. |

---

## Table of Contents

1. [Business Requirement Document (BRD)](#1-business-requirement-document-brd)
2. [System Architecture](#2-system-architecture)
3. [Project Structure](#3-project-structure)
4. [API Specification](#4-api-specification)
5. [CLI Reference](#5-cli-reference)
6. [Service Layer](#6-service-layer)
7. [Data Schemas & Validation](#7-data-schemas--validation)
8. [Template Architecture](#8-template-architecture)
9. [LLM Strategy & Prompt Design](#9-llm-strategy--prompt-design)
10. [Error Handling & Edge Cases](#10-error-handling--edge-cases)
11. [Functional Requirements](#11-functional-requirements)
12. [Non-Functional Requirements](#12-non-functional-requirements)
13. [Use Cases](#13-use-cases)
14. [Testing Strategy](#14-testing-strategy)
15. [Logging & Observability](#15-logging--observability)
16. [Configuration Management](#16-configuration-management)
17. [Dependencies & Environment](#17-dependencies--environment)
18. [Software Design Principles](#18-software-design-principles)
19. [Future Improvements & Recommendations](#19-future-improvements--recommendations)
20. [Glossary](#20-glossary)

---

## 1. Business Requirement Document (BRD)

### 1.1 Objective

This system is a local coding agent that automates the **entire job application lifecycle** — from discovering jobs to submitting tailored CVs and cover letters. It scrapes LinkedIn job listings, scores them against the user's profile, generates ATS-optimized CVs, produces cover letters, and manages the full pipeline through a CSV-based job database.

The system is built on a **FastAPI service layer**, making all features accessible through both a **CLI** (for immediate use) and a **REST API** (for future frontend integration). The CLI is a thin client that calls the same service functions the API exposes. This means a React, Next.js, or any other frontend can be plugged in later without rewriting any business logic.

### 1.2 Problem Statement

The job application process has four time-consuming stages:

**Stage 1 — Discovery:** Manually browsing job boards. Time: 1–2 hours. Solution: `jobfind` scrapes LinkedIn via Apify.

**Stage 2 — Prioritization:** Mentally ranking jobs by fit. Time: 30 min. Solution: `jobsort` uses GPT-4.1-nano to score relevance.

**Stage 3 — CV Tailoring:** Rewriting the CV per job. Time: 30–60 min. Solution: `mkcv` generates tailored, ATS-optimized CVs.

**Stage 4 — Cover Letter:** Drafting per application. Time: 20–40 min. Solution: `mkcover` generates tailored cover letters.

Combined, this reduces per-application effort from ~2 hours to ~3 minutes.

### 1.3 Stakeholders

| Role | Name | Responsibility |
|------|------|----------------|
| Primary User | Tanzir Hossain | Maintains profile data, triggers scraping/scoring/generation |
| Coding Agent | (System) | Orchestrates all pipelines via service layer |
| Apify API | (External) | Scrapes LinkedIn job listings |
| GitHub API | (External) | Provides repository and contribution data |
| OpenAI API | (External) | CV generation (`gpt-4o`), job scoring (`gpt-4.1-nano`), cover letters |

### 1.4 Core Business Needs

1. **Single source of truth** — `personal.md` for all personal data.
2. **Automated job discovery** — `jobfind` scrapes LinkedIn via Apify, stores in CSV.
3. **Intelligent job scoring** — `jobsort` uses GPT-4.1-nano to score relevance.
4. **CSV-based job database** — All jobs in `jobs.csv`, managed via pandas.
5. **Automated project extraction** — `gitref` fetches GitHub repos.
6. **Intelligent CV tailoring** — `mkcv` generates ATS-optimized CVs via GPT-4o.
7. **Cover letter generation** — `mkcover` produces tailored cover letters.
8. **Professional PDF output** — LaTeX-compiled, ATS-parseable, selectable text.
9. **Deadline management** — `deadline_review` prunes expired jobs.
10. **API-first architecture** — Every feature is a service function exposed via FastAPI, making frontend integration trivial.

### 1.5 Success Criteria

| Metric | Target |
|--------|--------|
| Time from discovery to CV submission | Under 3 minutes per job |
| Job scraping throughput | 1,000 jobs per `jobfind` run |
| Scoring accuracy (user agrees with top-10) | 80%+ |
| ATS parse rate | 90%+ sections correctly parsed |
| API response time (non-scraping endpoints) | < 5 seconds |
| Frontend integration effort | Zero backend changes required |

### 1.6 High-Level Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│                       USER INTERFACE LAYER                          │
│                                                                     │
│   CLI (python cli.py ...)      or      REST API (FastAPI)           │
│   ↓                                    ↓                            │
│   Both call the same service layer     Both return same data        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        SERVICE LAYER                                │
│                                                                     │
│   job_service      → scrape, continue, deadline_review, get jobs    │
│   scoring_service  → score unscored jobs, get top matches           │
│   cv_service       → generate CV by job_id or manual file           │
│   cover_service    → generate cover letter by job_id or manual file │
│   github_service   → fetch repos, write github.md                   │
│   profile_service  → read/validate personal.md                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                           │
│                                                                     │
│   csv_manager    → pandas DataFrame operations for jobs.csv         │
│   llm_chains     → LangChain chain definitions (GPT-4o, 4.1-nano)  │
│   apify_client   → Apify API wrapper                                │
│   template_engine→ LaTeX variable replacement + compilation         │
│   parser         → Markdown file parsing                            │
│   config         → Settings from .env via Pydantic BaseSettings     │
└─────────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                  │
│                                                                     │
│   personal.md    github.md    jobs.csv    scrape_state/             │
│   cv_templates/  cover_templates/  generated_cv/  generated_cover/  │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.7 Scope Boundaries

**In scope for v4.0:**

- FastAPI server with REST API endpoints
- CLI as thin client calling service layer
- LinkedIn job scraping via Apify API
- CSV-based job storage with pandas
- Job relevance scoring via GPT-4.1-nano
- Deadline tracking and expired job removal
- Pagination and continuation for scraping
- GitHub project fetching
- ATS-optimized CV generation via GPT-4o
- Cover letter generation via GPT-4o
- Three predefined LaTeX CV templates + cover letter template
- Job ID-based referencing across all commands/endpoints
- LangChain for LLM orchestration
- Pydantic schemas for request/response validation
- Background tasks for long-running operations (scraping)

**Explicitly out of scope:**

- Frontend UI (the API is ready for it — building it is a separate project)
- Relational database (CSV is sufficient for single-user)
- WebSocket real-time updates (polling is fine for v4.0)
- Authentication/authorization (single-user local system)
- Multi-user support
- Automated application submission

---

## 2. System Architecture

### 2.1 Architecture Pattern — Service-Layered Monolith

The system follows a **three-layer architecture** within a single Python package:

```
┌──────────────────────────────────────────────┐
│              INTERFACE LAYER                  │
│                                              │
│  ┌─────────────┐    ┌────────────────────┐   │
│  │   CLI        │    │   FastAPI Router   │   │
│  │  (cli.py)    │    │   (api/routes/)    │   │
│  └──────┬───────┘    └────────┬───────────┘   │
│         │                     │               │
│         └─────────┬───────────┘               │
│                   │                           │
├───────────────────┼───────────────────────────┤
│              SERVICE LAYER                    │
│                   │                           │
│  ┌────────────────▼──────────────────────┐    │
│  │  services/                            │    │
│  │    job_service.py                     │    │
│  │    scoring_service.py                 │    │
│  │    cv_service.py                      │    │
│  │    cover_service.py                   │    │
│  │    github_service.py                  │    │
│  │    profile_service.py                 │    │
│  └────────────────┬──────────────────────┘    │
│                   │                           │
├───────────────────┼───────────────────────────┤
│           INFRASTRUCTURE LAYER                │
│                   │                           │
│  ┌────────────────▼──────────────────────┐    │
│  │  core/                                │    │
│  │    csv_manager.py                     │    │
│  │    llm_chains.py                      │    │
│  │    apify_client.py                    │    │
│  │    template_engine.py                 │    │
│  │    parser.py                          │    │
│  │    config.py                          │    │
│  └───────────────────────────────────────┘    │
└──────────────────────────────────────────────┘
```

**Why this pattern:**

- The service layer contains all business logic. It knows nothing about HTTP or CLI — it takes Python objects in and returns Python objects out.
- The CLI (`cli.py`) imports service functions directly and calls them. It formats the output for the terminal.
- The FastAPI routes (`api/routes/`) import the same service functions and wrap them in HTTP endpoints. They handle request parsing and JSON responses.
- This means **100% of the business logic is shared**. Adding a frontend requires zero backend changes — just call the existing API.

### 2.2 Dual Interface Design

The system exposes every feature through two interfaces simultaneously:

| Feature | CLI Command | API Endpoint |
|---------|-------------|--------------|
| Scrape jobs | `python cli.py jobfind 24h Dhaka remote 500` | `POST /api/jobs/scrape` |
| Continue scrape | `python cli.py jobfind continue prev 2000` | `POST /api/jobs/scrape/continue` |
| Deadline review | `python cli.py jobfind deadline_review` | `POST /api/jobs/deadline-review` |
| Score jobs | `python cli.py jobsort` | `POST /api/jobs/score` |
| List jobs | (open CSV in spreadsheet) | `GET /api/jobs?status=scored&sort=relevance_score&limit=20` |
| Get job detail | (look up in CSV) | `GET /api/jobs/{job_id}` |
| Generate CV | `python cli.py mkcv jobid-ACD123 t1` | `POST /api/cv/generate` |
| Generate cover letter | `python cli.py mkcover jobid-ACD123` | `POST /api/cover/generate` |
| Fetch GitHub repos | `python cli.py gitref` | `POST /api/github/refresh` |
| Get profile | (open personal.md) | `GET /api/profile` |
| Download CV PDF | (open file) | `GET /api/cv/{job_id}/download` |
| Download cover letter | (open file) | `GET /api/cover/{job_id}/download` |

Both interfaces call the same service functions. The CLI is for power users who prefer the terminal. The API is for programmatic access and future frontend integration.

### 2.3 Background Tasks

Long-running operations (scraping, batch scoring) are executed as **FastAPI background tasks** when triggered via the API. The API returns immediately with a task ID, and the client can poll for status.

| Operation | API Behavior | CLI Behavior |
|-----------|-------------|--------------|
| Job scraping | Returns task ID → poll `GET /api/tasks/{id}` | Blocks with progress bar |
| Batch scoring | Returns task ID → poll | Blocks with progress bar |
| CV generation | Synchronous (< 30s) | Synchronous |
| Cover letter | Synchronous (< 20s) | Synchronous |
| GitHub fetch | Synchronous (< 10s) | Synchronous |
| Deadline review | Synchronous (< 2s) | Synchronous |

### 2.4 External Services

#### Apify API — LinkedIn Job Scraping

| Property | Value |
|----------|-------|
| Purpose | Scrape LinkedIn job search results with full job details and company information |
| Actor | `curious_coder/linkedin-jobs-scraper` |
| Actor URL | `https://apify.com/curious_coder/linkedin-jobs-scraper` |
| API Endpoint | `https://api.apify.com/v2/acts/curious_coder~linkedin-jobs-scraper/runs` |
| Authentication | Apify API token (`APIFY_API_TOKEN`) |
| Pricing | $1.00 per 1,000 results |
| Fallback | If API fails, preserve existing `jobs.csv` and return error |

**Data returned per job listing:** `id`, `title`, `companyName`, `companyLinkedinUrl`, `companyLogo`, `location`, `salaryInfo`, `postedAt`, `benefits`, `descriptionHtml`, `descriptionText`, `applicantsCount`, `applyUrl`, `jobPosterName`, `jobPosterTitle`, `jobPosterProfileUrl`, `seniorityLevel`, `employmentType`, `jobFunction`, `industries`, `companyDescription`, `companyWebsite`, `companyEmployeesCount`, `link`.

#### GitHub API

| Property | Value |
|----------|-------|
| Purpose | Fetch repository list, metadata, languages, descriptions |
| API Version | REST v3 (`api.github.com`) |
| Authentication | Personal Access Token (`GITHUB_PAT_TOKEN`) |
| Rate Limit | 5,000 requests/hour |
| Fallback | Use existing `github.md` and log warning |

#### OpenAI API

| Task | Model | Reason |
|------|-------|--------|
| CV content generation | `gpt-4o` | High quality for professional documents |
| Cover letter generation | `gpt-4o` | High quality for professional documents |
| Job relevance scoring | `gpt-4.1-nano` | Cost-efficient for batch scoring |

| Property | Value |
|----------|-------|
| Authentication | `OPENAI_API_KEY` |
| Retry Strategy | Exponential backoff (2s, 4s, 8s), max 3 retries |

**Token budgets:**

| Operation | Model | Input | Output | Cost |
|-----------|-------|-------|--------|------|
| CV generation | gpt-4o | ~3,000 | ~2,000 | ~$0.03 |
| Cover letter | gpt-4o | ~3,000 | ~500 | ~$0.02 |
| Scoring (10 jobs) | gpt-4.1-nano | ~2,000 | ~300 | ~$0.001 |
| Scoring (1,000 jobs) | gpt-4.1-nano | — | — | ~$0.10 |

---

## 3. Project Structure

```
job_agent/
│
├── app/                                 # Main application package
│   ├── __init__.py
│   ├── main.py                          # FastAPI app factory + startup
│   │
│   ├── api/                             # API interface layer
│   │   ├── __init__.py
│   │   ├── deps.py                      # Dependency injection (settings, services)
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── jobs.py                  # /api/jobs/* endpoints
│   │       ├── cv.py                    # /api/cv/* endpoints
│   │       ├── cover.py                 # /api/cover/* endpoints
│   │       ├── github.py               # /api/github/* endpoints
│   │       ├── profile.py              # /api/profile/* endpoints
│   │       └── tasks.py                # /api/tasks/* endpoints (background task status)
│   │
│   ├── services/                        # Business logic layer
│   │   ├── __init__.py
│   │   ├── job_service.py               # Scraping, searching, deadline review
│   │   ├── scoring_service.py           # Job relevance scoring
│   │   ├── cv_service.py                # CV generation pipeline
│   │   ├── cover_service.py             # Cover letter generation pipeline
│   │   ├── github_service.py            # GitHub project fetching
│   │   └── profile_service.py           # Profile reading and validation
│   │
│   ├── core/                            # Infrastructure layer
│   │   ├── __init__.py
│   │   ├── config.py                    # Pydantic BaseSettings (loads .env)
│   │   ├── csv_manager.py               # pandas DataFrame operations
│   │   ├── llm_chains.py                # LangChain chain definitions
│   │   ├── apify_client.py              # Apify API wrapper
│   │   ├── template_engine.py           # LaTeX variable replacement + compilation
│   │   └── parser.py                    # Markdown file parsing utilities
│   │
│   └── schemas/                         # Pydantic models for request/response
│       ├── __init__.py
│       ├── job.py                       # JobCreate, JobResponse, JobListResponse, ScrapeRequest
│       ├── cv.py                        # CVGenerateRequest, CVGenerateResponse
│       ├── cover.py                     # CoverGenerateRequest, CoverGenerateResponse
│       ├── scoring.py                   # ScoreRequest, ScoreResponse
│       ├── github.py                    # GitHubRefreshResponse
│       ├── profile.py                   # ProfileResponse
│       └── task.py                      # TaskStatus, TaskResponse
│
├── cli.py                               # CLI thin client (calls services directly)
│
├── data/                                # All persistent data files
│   ├── personal.md                      # Single source of truth for personal data
│   ├── github.md                        # Auto-generated project references
│   ├── jobs.csv                         # Scraped job database
│   └── scrape_state/
│       └── last_run.json                # Pagination state for continue
│
├── templates/                           # All LaTeX templates
│   ├── cv/
│   │   ├── cv_template_1.tex            # Standard ATS Clean Format
│   │   ├── cv_template_2.tex            # Skills-Focused CV
│   │   └── cv_template_3.tex            # Experience-Focused CV
│   └── cover/
│       └── cover_template_1.tex         # Standard cover letter
│
├── output/                              # All generated files
│   ├── cv/
│   │   └── Facebook_DataLabelingAnalyst_2026_03_05.pdf
│   └── cover/
│       └── Facebook_DataLabelingAnalyst_2026_03_05.pdf
│
├── job_circular/                        # Manually created job circulars (legacy)
│   └── BRAC_IT_Software_Engineer_2026_03_05.md
│
├── logs/
│   └── agent.log
│
├── tests/                               # Test suite
│   ├── __init__.py
│   ├── conftest.py                      # Shared fixtures (mock services, test client)
│   ├── test_services/
│   │   ├── test_job_service.py
│   │   ├── test_scoring_service.py
│   │   ├── test_cv_service.py
│   │   ├── test_cover_service.py
│   │   ├── test_github_service.py
│   │   └── test_profile_service.py
│   ├── test_core/
│   │   ├── test_csv_manager.py
│   │   ├── test_llm_chains.py
│   │   ├── test_template_engine.py
│   │   └── test_parser.py
│   └── test_api/
│       ├── test_jobs_routes.py
│       ├── test_cv_routes.py
│       └── test_cover_routes.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml                       # Python package config
└── README.md
```

### 3.1 Key Structural Decisions

**`app/` as a proper Python package:** The entire application lives inside `app/`. This makes imports clean (`from app.services.cv_service import generate_cv`), enables proper packaging, and follows FastAPI conventions.

**`data/` directory for all persistent files:** All user data (`personal.md`, `github.md`, `jobs.csv`) lives in `data/`. This separates data from code, makes backups trivial, and keeps the project root clean. The path is configurable via `DATA_DIR` in `.env`.

**`templates/` directory with subdirectories:** LaTeX templates are organized by type (`cv/`, `cover/`). This is cleaner than a flat directory and scales to future template types (e.g., `portfolio/`, `letter/`).

**`output/` directory with subdirectories:** Generated PDFs are organized by type (`cv/`, `cover/`). Keeps generated artifacts separate from source data.

**`tests/` mirrors `app/` structure:** Tests are organized to match the source structure (`test_services/`, `test_core/`, `test_api/`), making it easy to find the test for any module.

**`cli.py` at the project root:** The CLI entry point sits at the root for easy execution (`python cli.py ...`). It imports from `app.services` directly — it does not go through HTTP.

### 3.2 How CLI and API Share Logic

```python
# ── app/services/cv_service.py ──
# Pure business logic. No knowledge of HTTP or CLI.

from app.core.csv_manager import get_job_by_id
from app.core.parser import read_personal_md, read_github_md
from app.core.llm_chains import cv_generation_chain
from app.core.template_engine import fill_template, compile_latex

def generate_cv(job_id: str, template: str) -> dict:
    """Generate a tailored CV. Returns {"pdf_path": "...", "job_title": "..."}"""
    job = get_job_by_id(job_id)
    profile = read_personal_md()
    github = read_github_md()
    content = cv_generation_chain.invoke({...})
    tex_path = fill_template(template, content)
    pdf_path = compile_latex(tex_path)
    return {"pdf_path": pdf_path, "job_title": job["title"]}
```

```python
# ── app/api/routes/cv.py ──
# FastAPI route. Thin wrapper around the service.

from fastapi import APIRouter
from app.services.cv_service import generate_cv
from app.schemas.cv import CVGenerateRequest, CVGenerateResponse

router = APIRouter(prefix="/api/cv", tags=["CV"])

@router.post("/generate", response_model=CVGenerateResponse)
def api_generate_cv(req: CVGenerateRequest):
    result = generate_cv(job_id=req.job_id, template=req.template)
    return CVGenerateResponse(**result)
```

```python
# ── cli.py ──
# CLI client. Also a thin wrapper around the service.

from app.services.cv_service import generate_cv

def handle_mkcv(args):
    result = generate_cv(job_id=args.job_id, template=args.template)
    print(f"CV generated: {result['pdf_path']}")
```

**The service function is identical in both paths.** This is the core architectural guarantee.

---

## 4. API Specification

### 4.1 Server Configuration

| Property | Value |
|----------|-------|
| Framework | FastAPI |
| Host | `127.0.0.1` (localhost only — single user) |
| Port | `8000` (configurable via `.env`) |
| Docs | Swagger UI at `/docs`, ReDoc at `/redoc` |
| CORS | Enabled for `localhost:*` (for local frontend dev) |

**Starting the server:**

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 4.2 Endpoint Reference

#### Jobs

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|-------------|----------|
| `POST` | `/api/jobs/scrape` | Start LinkedIn scrape | `ScrapeRequest` | `TaskResponse` |
| `POST` | `/api/jobs/scrape/continue` | Continue previous scrape | `ScrapeContinueRequest` | `TaskResponse` |
| `POST` | `/api/jobs/deadline-review` | Mark expired jobs | — | `DeadlineReviewResponse` |
| `GET` | `/api/jobs` | List jobs (filtered, sorted, paginated) | Query params | `JobListResponse` |
| `GET` | `/api/jobs/{job_id}` | Get single job detail | — | `JobResponse` |

#### Scoring

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|-------------|----------|
| `POST` | `/api/jobs/score` | Score all unscored jobs | — | `TaskResponse` |
| `GET` | `/api/jobs/top` | Get top N scored jobs | `?limit=10` | `JobListResponse` |

#### CV

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|-------------|----------|
| `POST` | `/api/cv/generate` | Generate CV | `CVGenerateRequest` | `CVGenerateResponse` |
| `GET` | `/api/cv/{job_id}/download` | Download CV PDF | — | PDF file |

#### Cover Letter

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|-------------|----------|
| `POST` | `/api/cover/generate` | Generate cover letter | `CoverGenerateRequest` | `CoverGenerateResponse` |
| `GET` | `/api/cover/{job_id}/download` | Download cover letter PDF | — | PDF file |

#### GitHub

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `POST` | `/api/github/refresh` | Fetch repos, update github.md | `GitHubRefreshResponse` |

#### Profile

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/api/profile` | Get parsed personal profile | `ProfileResponse` |

#### Tasks (Background)

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/api/tasks/{task_id}` | Check status of background task | `TaskStatusResponse` |

### 4.3 Pydantic Schemas

#### `ScrapeRequest`

```python
class ScrapeRequest(BaseModel):
    deadline: Literal["24h", "7d", "30d", "anytime"]
    location: str                          # e.g., "Bangladesh", "Dhaka"
    role: str | None = None                # e.g., "Software Engineer"
    work_type: Literal["onsite", "hybrid", "remote"] | None = None
    limit: int = Field(ge=1, le=5000)      # Max jobs to scrape
```

#### `ScrapeContinueRequest`

```python
class ScrapeContinueRequest(BaseModel):
    new_limit: int = Field(ge=1, le=10000) # Must be > previous limit
```

#### `CVGenerateRequest`

```python
class CVGenerateRequest(BaseModel):
    job_id: str | None = None              # e.g., "ACD123" (from CSV)
    job_file: str | None = None            # e.g., "BRAC_IT_Software_Engineer_2026_03_05.md"
    template: Literal["t1", "t2", "t3"]

    @model_validator(mode="after")
    def check_job_reference(self):
        if not self.job_id and not self.job_file:
            raise ValueError("Provide either job_id or job_file")
        if self.job_id and self.job_file:
            raise ValueError("Provide only one of job_id or job_file")
        return self
```

#### `CoverGenerateRequest`

```python
class CoverGenerateRequest(BaseModel):
    job_id: str | None = None
    job_file: str | None = None

    @model_validator(mode="after")
    def check_job_reference(self):
        if not self.job_id and not self.job_file:
            raise ValueError("Provide either job_id or job_file")
        if self.job_id and self.job_file:
            raise ValueError("Provide only one of job_id or job_file")
        return self
```

#### `JobResponse`

```python
class JobResponse(BaseModel):
    job_id: str
    linkedin_id: str
    title: str
    company_name: str
    company_website: str | None
    location: str
    work_type: str | None
    seniority_level: str | None
    employment_type: str | None
    salary_min: str | None
    salary_max: str | None
    description_text: str
    posted_at: str | None
    deadline: str | None
    apply_url: str | None
    linkedin_url: str
    poster_name: str | None
    poster_title: str | None
    relevance_score: float | None
    score_reason: str | None
    status: str
    cv_generated: bool
    cover_generated: bool
```

#### `JobListResponse`

```python
class JobListResponse(BaseModel):
    total: int
    jobs: list[JobResponse]
```

#### `CVGenerateResponse`

```python
class CVGenerateResponse(BaseModel):
    pdf_path: str
    job_id: str
    job_title: str
    company_name: str
    template_used: str
```

#### `TaskResponse`

```python
class TaskResponse(BaseModel):
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    message: str | None = None
```

#### `TaskStatusResponse`

```python
class TaskStatusResponse(BaseModel):
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    progress: float | None = None          # 0.0 to 1.0
    result: dict | None = None             # Final result when completed
    error: str | None = None               # Error message if failed
```

### 4.4 Query Parameters for `GET /api/jobs`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | String | — | Filter by status: `new`, `scored`, `applied`, `expired` |
| `min_score` | Float | — | Minimum relevance score |
| `sort` | String | `relevance_score` | Sort field |
| `order` | String | `desc` | `asc` or `desc` |
| `limit` | Integer | 50 | Page size |
| `offset` | Integer | 0 | Pagination offset |
| `search` | String | — | Search in title, company_name, description_text |

---

## 5. CLI Reference

The CLI is a thin client that imports and calls service functions directly. It does not go through HTTP — it calls Python functions in-process for maximum speed.

**Entry point:** `python cli.py <command> [args]`

### 5.1 Commands

#### `jobfind` — Scrape LinkedIn Jobs

```bash
python cli.py jobfind <deadline> <location> [role] [work_type] <limit>
```

| Parameter | Required | Values | Description |
|-----------|----------|--------|-------------|
| `deadline` | Yes | `24h`, `7d`, `30d`, `anytime` | LinkedIn date filter |
| `location` | Yes | Any string | Location filter |
| `role` | No | Any string | Job title or keyword |
| `work_type` | No | `onsite`, `hybrid`, `remote` | Workplace type |
| `limit` | Yes | Integer | Max jobs to scrape |

**Examples:**

```bash
python cli.py jobfind 24h Bangladesh "Software Engineer" remote 500
python cli.py jobfind 7d Dhaka 1000
python cli.py jobfind 24h Bangladesh "AI Engineer" onsite 200
```

#### `jobfind continue` — Continue Previous Scrape

```bash
python cli.py jobfind continue prev <new_limit>
```

```bash
python cli.py jobfind continue prev 2000
```

#### `jobfind deadline_review` — Remove Expired Jobs

```bash
python cli.py jobfind deadline_review
```

#### `jobsort` — Score Jobs by Relevance

```bash
python cli.py jobsort
```

#### `gitref` — Fetch GitHub Projects

```bash
python cli.py gitref
```

#### `mkcv` — Generate CV

```bash
# By job ID (from CSV)
python cli.py mkcv jobid-ACD123 t1

# By manual file (legacy)
python cli.py mkcv BRAC_IT_Software_Engineer_2026_03_05.md t1
```

#### `mkcover` — Generate Cover Letter

```bash
# By job ID
python cli.py mkcover jobid-ACD123

# By manual file
python cli.py mkcover BRAC_IT_Software_Engineer_2026_03_05.md
```

---

## 6. Service Layer

Each service module is a collection of pure functions (or a class with injected dependencies). Services know nothing about HTTP or CLI — they accept Python objects and return Python objects.

### 6.1 `job_service.py`

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `scrape_jobs(deadline, location, role, work_type, limit)` | Filter params | `{new_count, duplicate_count, total_count}` | Calls Apify, deduplicates, assigns IDs, appends to CSV |
| `continue_scrape(new_limit)` | New limit | `{new_count, duplicate_count, total_count}` | Reads last_run.json, resumes from offset |
| `deadline_review()` | — | `{expired_count, active_count}` | Marks expired jobs in CSV |
| `get_jobs(status, min_score, sort, order, limit, offset, search)` | Filter/sort params | `{total, jobs: [...]}` | Reads and filters CSV |
| `get_job(job_id)` | Job ID string | `JobDict` or raises `NotFoundError` | Looks up single row |

### 6.2 `scoring_service.py`

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `score_all_unscored()` | — | `{scored_count, top_5: [...]}` | Reads CSV + personal.md, batches to GPT-4.1-nano, writes scores |
| `rescore_all()` | — | Same | Clears all scores, re-scores everything |
| `get_top_jobs(limit)` | Integer | `[JobDict, ...]` | Returns top N scored jobs |

### 6.3 `cv_service.py`

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `generate_cv(job_id, template)` | ID + template string | `{pdf_path, job_title, company}` | Full pipeline: resolve job → LLM → template → compile |
| `generate_cv_from_file(file_path, template)` | Path + template | Same | Legacy mode for manual .md files |

### 6.4 `cover_service.py`

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `generate_cover(job_id)` | Job ID | `{pdf_path, job_title, company}` | Full pipeline for cover letters |
| `generate_cover_from_file(file_path)` | Path | Same | Legacy mode |

### 6.5 `github_service.py`

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `refresh_github()` | — | `{repo_count, file_path}` | Fetches all repos, writes github.md |

### 6.6 `profile_service.py`

| Function | Input | Output | Description |
|----------|-------|--------|-------------|
| `get_profile()` | — | Parsed profile dict | Reads and validates personal.md |
| `validate_profile()` | — | `{valid: bool, errors: [...]}` | Validates without returning data |

---

## 7. Data Schemas & Validation

### 7.1 `personal.md` Validation

| Rule | Check | Error |
|------|-------|-------|
| File exists | Present in `data/` | `ERROR: personal.md not found in data/ directory.` |
| Required sections | Personal Information, Skills, Experience, Education | `ERROR: Missing required section: [name]` |
| Name present | Non-empty | `ERROR: Name is missing` |
| Email format | Basic regex | `WARNING: Invalid email format` |
| At least one skill | Skills section non-empty | `ERROR: No skills found` |
| At least one experience | Experience section non-empty | `ERROR: No experience found` |

### 7.2 `jobs.csv` Schema

| Column | Type | Source | Description |
|--------|------|--------|-------------|
| `job_id` | String | Agent-generated | Unique ID (e.g., `ACD123`) |
| `linkedin_id` | String | Apify | LinkedIn job ID |
| `title` | String | Apify | Job title |
| `company_name` | String | Apify | Company name |
| `company_linkedin_url` | String | Apify | Company LinkedIn URL |
| `company_website` | String | Apify | Company website |
| `company_logo` | String | Apify | Logo URL |
| `company_description` | String | Apify | Company about |
| `company_employees_count` | Integer | Apify | Employee count |
| `location` | String | Apify | Job location |
| `work_type` | String | Inferred | `onsite`, `hybrid`, `remote` |
| `salary_min` | String | Apify | Min salary |
| `salary_max` | String | Apify | Max salary |
| `seniority_level` | String | Apify | Seniority |
| `employment_type` | String | Apify | Full-time, Contract, etc. |
| `job_function` | String | Apify | Job function |
| `industries` | String | Apify | Industry |
| `description_text` | String | Apify | Full description (plain text) |
| `description_html` | String | Apify | Full description (HTML) |
| `applicants_count` | String | Apify | Applicant count |
| `posted_at` | Date | Apify | Posted date |
| `deadline` | Date | Inferred | Deadline (`posted_at + 30d` if missing) |
| `apply_url` | String | Apify | Application URL |
| `linkedin_url` | String | Apify | LinkedIn job URL |
| `poster_name` | String | Apify | Recruiter name |
| `poster_title` | String | Apify | Recruiter title |
| `poster_profile_url` | String | Apify | Recruiter profile URL |
| `relevance_score` | Float | GPT-4.1-nano | 0.0–100.0 |
| `score_reason` | String | GPT-4.1-nano | Brief explanation |
| `scraped_at` | Datetime | Agent | Scrape timestamp |
| `cv_generated` | Boolean | Agent | CV exists for this job |
| `cover_generated` | Boolean | Agent | Cover letter exists |
| `status` | String | Agent | `new`, `scored`, `applied`, `rejected`, `expired` |

### 7.3 Job ID Generation

```python
import hashlib

def generate_job_id(linkedin_id: str) -> str:
    return hashlib.md5(linkedin_id.encode()).hexdigest()[:6].upper()
```

Collision handling: append `-2` suffix if ID already exists in CSV.

### 7.4 Validation Rules Summary

| Command/Endpoint | Validations |
|-----------------|-------------|
| `jobfind` / `POST /api/jobs/scrape` | deadline ∈ {24h,7d,30d,anytime}, limit > 0, work_type ∈ {onsite,hybrid,remote} if given |
| `jobfind continue` | last_run.json exists, new_limit > previous_limit |
| `jobsort` / `POST /api/jobs/score` | jobs.csv exists, personal.md exists and valid |
| `mkcv` / `POST /api/cv/generate` | job_id exists in CSV or file exists, template ∈ {t1,t2,t3}, personal.md valid |
| `mkcover` / `POST /api/cover/generate` | job_id exists in CSV or file exists, personal.md valid |
| `gitref` / `POST /api/github/refresh` | GITHUB_PAT_TOKEN set in .env |

---

## 8. Template Architecture

### 8.1 Design Philosophy

All LaTeX layout is predefined. The agent only performs variable replacement — never dynamic LaTeX generation. Templates live in `templates/cv/` and `templates/cover/`.

### 8.2 CV Templates

| Template | Shorthand | Focus |
|----------|-----------|-------|
| `cv_template_1.tex` | `t1` | Standard ATS Clean Format |
| `cv_template_2.tex` | `t2` | Skills-Focused CV |
| `cv_template_3.tex` | `t3` | Experience-Focused CV |

### 8.3 Cover Letter Template

`cover_template_1.tex` — Standard professional cover letter with header, salutation, 3–4 paragraph body, closing.

### 8.4 Template Variable Reference

All variables use `{{VARIABLE_NAME}}` syntax.

**Identity Variables:** `{{NAME}}`, `{{EMAIL}}`, `{{PHONE}}`, `{{LINKEDIN}}`, `{{GITHUB}}`, `{{LOCATION}}`, `{{PORTFOLIO}}`

**CV Content Variables (GPT-4o generated):** `{{SUMMARY}}`, `{{SKILLS}}`, `{{EXPERIENCE}}`, `{{PROJECTS}}`, `{{EDUCATION}}`, `{{CERTIFICATIONS}}`

**Cover Letter Variables (GPT-4o generated):** `{{COVER_DATE}}`, `{{COVER_SALUTATION}}`, `{{COVER_BODY}}`, `{{COVER_CLOSING}}`

**Job Context Variables:** `{{TARGET_ROLE}}`, `{{COMPANY_NAME}}`, `{{COMPANY_WEBSITE}}`

### 8.5 Variable Replacement Rules

1. All variables must be replaced. Missing data → empty string.
2. LaTeX special characters escaped: `&`, `%`, `$`, `#`, `_`, `{`, `}`, `~`, `^`, `\`.
3. Multi-line variables converted to LaTeX line breaks.
4. Agent verifies no `{{`/`}}` remain before compilation.

### 8.6 LaTeX Compilation

| Property | Value |
|----------|-------|
| Compiler | `pdflatex` |
| Passes | 2 |
| CV output | `output/cv/` |
| Cover output | `output/cover/` |
| On failure | Preserve `.tex`, return error with compiler output |

---

## 9. LLM Strategy & Prompt Design

### 9.1 LangChain Architecture

All LLM interactions are orchestrated through LangChain. Three chains are defined in `app/core/llm_chains.py`:

| Chain | Model | Temperature | Purpose |
|-------|-------|-------------|---------|
| `cv_generation_chain` | GPT-4o | 0.3 | Generate tailored CV content |
| `cover_letter_chain` | GPT-4o | 0.4 | Generate tailored cover letter |
| `job_scoring_chain` | GPT-4.1-nano | 0.1 | Score job relevance (batches of 10) |

**LangChain components used:** `ChatOpenAI`, `ChatPromptTemplate`, `StructuredOutputParser`, `RunnableSequence`, `RetryOutputParser`.

### 9.2 CV Generation Chain

**System prompt:** Expert ATS resume optimizer. Prioritizes job keywords, rewrites bullet points for relevance, selects relevant projects, uses action verbs, never fabricates.

**Output format:** `[SUMMARY]`, `[SKILLS]`, `[EXPERIENCE]`, `[PROJECTS]` sections parsed by `StructuredOutputParser`.

### 9.3 Cover Letter Chain

**System prompt:** Expert cover letter writer. Opens with genuine company interest (using `company_description`), connects experience to requirements, highlights 2–3 achievements, 250–350 words.

**Output format:** `[SALUTATION]`, `[BODY]`, `[CLOSING]` sections.

### 9.4 Job Scoring Chain

**System prompt:** Scoring system with weighted criteria — skills match (40%), experience level (25%), domain fit (15%), location (10%), role alignment (10%). Score 0.0–100.0.

**Input:** Batch of up to 10 jobs + candidate summary.
**Output:** JSON array of `{job_index, score, reason}`.

### 9.5 Response Parsing & Retry

All chains use `StructuredOutputParser`. On parse failure: retry once with correction prompt. On second failure: skip (scoring) or raise error (CV/cover).

---

## 10. Error Handling & Edge Cases

### 10.1 Error Response Format (API)

All API errors return a consistent JSON structure:

```json
{
  "detail": {
    "error_code": "JOB_NOT_FOUND",
    "message": "Job ID 'ACD123' not found in jobs.csv.",
    "suggestion": "Run 'python cli.py jobsort' to see available job IDs."
  }
}
```

The CLI prints the same `message` and `suggestion` fields to the terminal.

### 10.2 Error Categories

| Category | HTTP Status | CLI Exit Code | Behavior |
|----------|------------|---------------|----------|
| Missing `personal.md` | 422 | 1 | Return error with creation instructions |
| Missing `jobs.csv` | 422 | 1 | Suggest running `jobfind` |
| Job ID not found | 404 | 1 | Return error with the ID |
| Invalid arguments | 422 | 1 | Return validation errors |
| Apify failure | 502 | 1 | Preserve CSV, return Apify error |
| Apify timeout | 504 | 1 | Return timeout message |
| OpenAI failure (CV/cover) | 502 | 1 | After 3 retries, return error |
| OpenAI failure (scoring) | 207 | 0 | Skip failed jobs, continue, report count |
| LaTeX compilation failure | 500 | 1 | Preserve `.tex`, return compiler output |
| Unreplaced template variables | 500 | 1 | List which variables remain |
| CSV corruption | 500 | 1 | Return error, suggest restore |
| `.env` incomplete | 500 | 1 | List missing keys |

### 10.3 Edge Cases

**LinkedIn 1,000 result ceiling:** Warn user. Suggest different filters or location splitting.

**Duplicate jobs across runs:** Deduplicated by `linkedin_id`. Silently skipped. Count reported.

**No deadline in Apify data:** Default to `posted_at + 30 days`, flagged as inferred.

**Empty job description:** Set `relevance_score = null`, `score_reason = "Insufficient description"`.

**Scoring already-scored jobs:** `jobsort` skips scored rows. `--rescore` flag clears all scores first.

**Re-generating CV for same job:** Overwrites previous PDF. Prints/returns a note.

**Special characters in filenames:** Strip all non-alphanumeric except underscores.

---

## 11. Functional Requirements

| ID | Priority | Feature | Description |
|----|----------|---------|-------------|
| FR1 | Critical | Personal Info | User edits `data/personal.md`. Agent reads dynamically. |
| FR2 | Critical | Job Scraping | `jobfind` / `POST /api/jobs/scrape` scrapes LinkedIn via Apify. Supports filters, continuation, deadline review. |
| FR3 | Critical | Job Scoring | `jobsort` / `POST /api/jobs/score` scores unscored jobs via GPT-4.1-nano. |
| FR4 | High | GitHub Fetch | `gitref` / `POST /api/github/refresh` fetches repos, writes `github.md`. |
| FR5 | Critical | CV Generation | `mkcv` / `POST /api/cv/generate` generates tailored CV PDF via job ID or manual file. |
| FR6 | High | Cover Letter | `mkcover` / `POST /api/cover/generate` generates tailored cover letter PDF. |
| FR7 | High | Job Browsing | `GET /api/jobs` with filtering, sorting, pagination, search. |
| FR8 | High | File Download | `GET /api/cv/{id}/download` and `GET /api/cover/{id}/download` serve PDFs. |
| FR9 | Medium | Background Tasks | Scraping and scoring run as background tasks via API with status polling. |
| FR10 | High | Dual Interface | Every feature accessible via both CLI and REST API using shared service layer. |

---

## 12. Non-Functional Requirements

| ID | Category | Requirement | Target |
|----|----------|-------------|--------|
| NFR1 | Performance | API cold start | < 2 seconds |
| NFR2 | Performance | `GET /api/jobs` (10K rows) | < 500ms |
| NFR3 | Performance | CV generation (incl. LLM) | < 30 seconds |
| NFR4 | Performance | Cover letter generation | < 20 seconds |
| NFR5 | Performance | Batch scoring (100 jobs) | < 60 seconds |
| NFR6 | Performance | LaTeX compilation | < 5 seconds |
| NFR7 | Performance | Deadline review (10K rows) | < 2 seconds |
| NFR8 | Security | API keys in `.env` only | Never in code or logs |
| NFR9 | Security | API listens on localhost only | `127.0.0.1` |
| NFR10 | Cost | 1,000 jobs scored | < $0.15 |
| NFR11 | Cost | Single CV | < $0.05 |
| NFR12 | Maintainability | Each module < 250 lines | Verified |
| NFR13 | Maintainability | Service layer has zero HTTP/CLI imports | Verified |
| NFR14 | Portability | Linux, macOS, Windows | Tested |
| NFR15 | Extensibility | Adding a frontend requires zero backend changes | Guaranteed by architecture |

---

## 13. Use Cases

### UC1 — Discover Jobs (CLI)

```bash
python cli.py jobfind 24h Bangladesh "Software Engineer" remote 500
```

Service call: `job_service.scrape_jobs("24h", "Bangladesh", "Software Engineer", "remote", 500)`

### UC2 — Discover Jobs (API)

```bash
curl -X POST http://localhost:8000/api/jobs/scrape \
  -H "Content-Type: application/json" \
  -d '{"deadline":"24h","location":"Bangladesh","role":"Software Engineer","work_type":"remote","limit":500}'
```

Returns `TaskResponse` with `task_id`. Poll `GET /api/tasks/{task_id}` for completion.

### UC3 — Score Jobs

```bash
# CLI
python cli.py jobsort

# API
curl -X POST http://localhost:8000/api/jobs/score
```

Both call: `scoring_service.score_all_unscored()`

### UC4 — Browse Jobs (API)

```bash
curl "http://localhost:8000/api/jobs?status=scored&min_score=70&sort=relevance_score&order=desc&limit=10"
```

### UC5 — Generate CV

```bash
# CLI
python cli.py mkcv jobid-ACD123 t1

# API
curl -X POST http://localhost:8000/api/cv/generate \
  -H "Content-Type: application/json" \
  -d '{"job_id":"ACD123","template":"t1"}'
```

Both call: `cv_service.generate_cv("ACD123", "t1")`

### UC6 — Generate Cover Letter

```bash
# CLI
python cli.py mkcover jobid-ACD123

# API
curl -X POST http://localhost:8000/api/cover/generate \
  -H "Content-Type: application/json" \
  -d '{"job_id":"ACD123"}'
```

### UC7 — Download Generated PDF (API)

```bash
curl http://localhost:8000/api/cv/ACD123/download --output cv.pdf
```

### UC8 — Full Pipeline

```bash
python cli.py jobfind 7d Bangladesh "Backend Engineer" remote 500
python cli.py jobsort
# Review top jobs
python cli.py mkcv jobid-A3F2C1 t2
python cli.py mkcover jobid-A3F2C1
# Submit application with generated PDFs
```

---

## 14. Testing Strategy

### 14.1 Test Structure

```
tests/
├── conftest.py                  # FastAPI TestClient, mock services, fixtures
├── test_services/               # Unit tests for business logic
│   ├── test_job_service.py
│   ├── test_scoring_service.py
│   ├── test_cv_service.py
│   ├── test_cover_service.py
│   ├── test_github_service.py
│   └── test_profile_service.py
├── test_core/                   # Unit tests for infrastructure
│   ├── test_csv_manager.py
│   ├── test_llm_chains.py
│   ├── test_template_engine.py
│   └── test_parser.py
└── test_api/                    # Integration tests for API routes
    ├── test_jobs_routes.py
    ├── test_cv_routes.py
    └── test_cover_routes.py
```

### 14.2 Testing Approach

**Service tests** — Unit tests with mocked infrastructure (mocked LLM chains, mocked Apify, mocked file I/O). These test pure business logic.

**Core tests** — Unit tests for CSV operations, template replacement, Markdown parsing. These use real files in a temp directory.

**API tests** — Integration tests using FastAPI `TestClient`. Mock the service layer. Verify HTTP status codes, response schemas, and error formats.

**Key test cases:**

| Module | Cases |
|--------|-------|
| `job_service` | Scrape with mocked Apify. Deduplication. Continue from state. Deadline review logic. |
| `scoring_service` | Batch scoring with mocked LLM. Skip already-scored. Sort order. |
| `cv_service` | Resolve job from CSV. Resolve from file. LLM → template → compile flow. |
| `csv_manager` | Create/append/deduplicate/lookup/update. Schema enforcement. Round-trip integrity. |
| `template_engine` | Replace all variables. LaTeX escaping. Empty optionals. No `{{` remaining. |
| API routes | Correct status codes. Pydantic validation. Error response format. File download. |

### 14.3 Manual Checklist

- [ ] Start server: `uvicorn app.main:app --reload`
- [ ] Hit `/docs` — verify Swagger UI loads with all endpoints
- [ ] `POST /api/jobs/scrape` — verify task created
- [ ] `GET /api/tasks/{id}` — verify status progression
- [ ] `GET /api/jobs` — verify pagination and filtering
- [ ] `POST /api/cv/generate` — verify PDF returned
- [ ] `GET /api/cv/{id}/download` — verify PDF download
- [ ] All CLI commands — verify same results as API
- [ ] Generate CV with all 3 templates — verify different layouts
- [ ] Upload to ATS simulator — verify >90% parse rate

---

## 15. Logging & Observability

### 15.1 Configuration

| Property | Value |
|----------|-------|
| Log file | `logs/agent.log` |
| Rotation | 5 MB, 3 backups |
| Format | `[YYYY-MM-DD HH:MM:SS] [LEVEL] [module] message` |
| Console | INFO+ |
| File | DEBUG+ |
| FastAPI access log | Enabled (request method, path, status, duration) |

### 15.2 Sensitive Data Policy

API keys, emails, phone numbers, and PII never appear in logs. Logs contain file paths, job IDs, token counts, and timing — not content.

---

## 16. Configuration Management

### 16.1 Settings via Pydantic BaseSettings

All configuration is managed through a Pydantic `BaseSettings` class in `app/core/config.py`. This loads values from `.env` with type validation and defaults.

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Required
    GITHUB_PAT_TOKEN: str
    OPENAI_API_KEY: str
    APIFY_API_TOKEN: str

    # Server
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Paths
    DATA_DIR: str = "data"
    TEMPLATES_DIR: str = "templates"
    OUTPUT_DIR: str = "output"
    LOGS_DIR: str = "logs"

    # OpenAI
    OPENAI_CV_MODEL: str = "gpt-4o"
    OPENAI_SCORING_MODEL: str = "gpt-4.1-nano"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_CV_TEMPERATURE: float = 0.3
    OPENAI_SCORING_TEMPERATURE: float = 0.1
    OPENAI_COVER_TEMPERATURE: float = 0.4

    # GitHub
    GITHUB_USERNAME: str = ""

    # Apify
    APIFY_POLL_INTERVAL_SECONDS: int = 10
    APIFY_TIMEOUT_SECONDS: int = 600

    # Defaults
    DEFAULT_DEADLINE_DAYS: int = 30
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

### 16.2 `.env.example`

```env
# Required
GITHUB_PAT_TOKEN=
OPENAI_API_KEY=
APIFY_API_TOKEN=

# Server
HOST=127.0.0.1
PORT=8000

# Paths (relative to project root)
DATA_DIR=data
TEMPLATES_DIR=templates
OUTPUT_DIR=output

# OpenAI
OPENAI_CV_MODEL=gpt-4o
OPENAI_SCORING_MODEL=gpt-4.1-nano
OPENAI_MAX_TOKENS=4000
OPENAI_CV_TEMPERATURE=0.3
OPENAI_SCORING_TEMPERATURE=0.1
OPENAI_COVER_TEMPERATURE=0.4

# GitHub
GITHUB_USERNAME=your_github_username

# Apify
APIFY_POLL_INTERVAL_SECONDS=10
APIFY_TIMEOUT_SECONDS=600

# Defaults
DEFAULT_DEADLINE_DAYS=30
LOG_LEVEL=INFO
```

### 16.3 `.gitignore`

```gitignore
.env
data/jobs.csv
data/scrape_state/
output/
logs/
__pycache__/
*.aux
*.log
*.out
*.pyc
.pytest_cache/
```

---

## 17. Dependencies & Environment

### 17.1 System Requirements

| Requirement | Minimum |
|-------------|---------|
| Python | 3.11+ |
| TeX Live (or MiKTeX) | With `pdflatex` |
| OS | Linux, macOS, Windows |
| Internet | Required for API calls |

### 17.2 Python Dependencies (`requirements.txt`)

```
# Web Framework
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0

# LLM Orchestration
langchain>=0.2.0
langchain-openai>=0.1.0
openai>=1.12.0

# Data Management
pandas>=2.2.0

# Scraping
apify-client>=1.6.0

# HTTP
requests>=2.31.0
httpx>=0.27.0

# Testing
pytest>=8.0.0
pytest-asyncio>=0.23.0

# Utilities
python-dotenv>=1.0.0
```

### 17.3 Tech Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **API Framework** | **FastAPI** | REST API with auto-generated docs, Pydantic validation, background tasks |
| **Server** | **Uvicorn** | ASGI server for FastAPI |
| **Validation** | **Pydantic** | Request/response schemas, settings management |
| **LLM Orchestration** | **LangChain** | Prompt templates, output parsing, chain composition |
| **Data Management** | **pandas** | CSV read/write, filtering, sorting, deduplication |
| **LinkedIn Scraping** | **Apify API** | `curious_coder/linkedin-jobs-scraper` actor |
| **CV/Cover Generation** | **OpenAI GPT-4o** | Professional content generation |
| **Job Scoring** | **OpenAI GPT-4.1-nano** | Cost-efficient batch relevance scoring |
| **Documents** | **LaTeX** (`pdflatex`) | PDF compilation |
| **Configuration** | **Pydantic BaseSettings** | Typed env variable management |
| **Testing** | **pytest** + FastAPI `TestClient` | Unit and integration tests |

### 17.4 Setup Steps

```bash
# 1. Clone
git clone https://github.com/tanzirhossain/job_agent.git
cd job_agent

# 2. Virtual environment
python -m venv venv
source venv/bin/activate

# 3. Install
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Edit .env with your API keys

# 5. Verify LaTeX
pdflatex --version

# 6. Start the API server (optional — only needed if using API/frontend)
uvicorn app.main:app --reload

# 7. Or use CLI directly
python cli.py gitref
python cli.py jobfind 7d Bangladesh "Software Engineer" remote 500
python cli.py jobsort
python cli.py mkcv jobid-A3F2C1 t1
python cli.py mkcover jobid-A3F2C1
```

---

## 18. Software Design Principles

### 18.1 KISS — Keep It Simple

CSV for jobs. Markdown for profiles. LaTeX for PDFs. FastAPI for the API. The service layer is plain Python functions. No ORM, no event bus, no message queue, no Docker-in-Docker.

### 18.2 Occam's Razor

CSV over SQLite — inspectable in any spreadsheet. FastAPI over Django — lighter, faster, better for APIs. Pydantic over manual validation — less code, better errors. Apify over a custom scraper — they handle anti-bot, we handle logic.

### 18.3 DRY

All business logic lives in `app/services/`. The CLI and API are thin wrappers — neither contains logic. Shared infrastructure (`csv_manager`, `llm_chains`, `template_engine`, `parser`) is imported by services, never duplicated.

### 18.4 YAGNI

No auth (single user). No WebSockets (polling is fine). No database (CSV is sufficient). No frontend (the API is ready for one, but building it is a separate project). No Docker (runs directly on the machine).

### 18.5 Separation of Concerns

```
Interface Layer    →  Knows HTTP/CLI. Knows nothing about business logic.
Service Layer      →  Knows business logic. Knows nothing about HTTP/CLI.
Infrastructure     →  Knows APIs/files/LLMs. Knows nothing about business rules.
```

| Module | Layer | Responsibility | Never Imports From |
|--------|-------|----------------|--------------------|
| `api/routes/*.py` | Interface | HTTP request handling | `core/` (goes through services) |
| `cli.py` | Interface | Terminal I/O | `core/` (goes through services) |
| `services/*.py` | Service | Business logic | `api/`, `cli.py` |
| `core/*.py` | Infrastructure | File I/O, API calls, LLM | `api/`, `cli.py`, `services/` |
| `schemas/*.py` | Shared | Data validation | — |

This strict layering means:

- **Adding a frontend** → Add API calls from the frontend. Zero backend changes.
- **Swapping CSV for SQLite** → Rewrite `csv_manager.py`. Services and API unchanged.
- **Switching from OpenAI to Anthropic** → Rewrite `llm_chains.py`. Services and API unchanged.
- **Adding a new command** → Add a service function + API route + CLI handler. Existing code unchanged.

### 18.6 Fail Fast, Fail Clearly

Pydantic validates all API requests before they reach the service layer. Services validate business rules (file exists, job ID exists) before calling infrastructure. Errors propagate up with clear messages and suggestions for the user.

---

## 19. Future Improvements & Recommendations

### 19.1 Short-Term (v4.1)

**Response caching:** Cache GPT-4o responses per job_id so template changes don't require re-calling the LLM.

**Batch generation:** `POST /api/cv/generate-batch` with `{"job_ids": [...], "template": "t1"}`.

**CSV export:** `GET /api/jobs/export?format=xlsx` for Excel export.

**Rescore endpoint:** `POST /api/jobs/rescore` to clear and regenerate all scores.

### 19.2 Medium-Term (v5.0)

**Frontend:** React/Next.js dashboard consuming the existing API. Job table with sorting/filtering, one-click CV generation, PDF preview.

**WebSocket progress:** Replace polling with WebSocket for real-time task progress (scraping, scoring).

**Application tracker:** Status workflow: `new` → `scored` → `applied` → `interviewing` → `offered` → `rejected`.

**SQLite migration:** If CSV performance degrades at scale, migrate `csv_manager.py` to SQLite. Service layer unchanged.

**BDJobs / Indeed scrapers:** Add Apify actors for other job boards.

### 19.3 Long-Term (v6.0+)

**Local LLM:** Ollama/LM Studio as OpenAI alternative.

**Multi-user:** Auth + per-user data directories.

**Automated submission:** Browser automation for application forms.

**Interview prep:** `POST /api/interview/generate` produces talking points.

### 19.4 Architecture Notes

**The FastAPI structure makes the frontend transition trivial.** When you're ready to build a React frontend, you don't touch any backend code. You just make HTTP calls to the same endpoints documented in Section 4. The Swagger docs at `/docs` serve as a live, interactive API reference for frontend development.

**CORS is pre-configured** for `localhost:*` — a local React dev server (typically `localhost:3000`) can call the API immediately.

---

## 20. Glossary

| Term | Definition |
|------|-----------|
| **Apify** | Cloud platform for web scraping. Uses the `curious_coder/linkedin-jobs-scraper` actor. |
| **ATS** | Applicant Tracking System — parses and ranks resumes. |
| **Background Task** | A FastAPI feature for running long operations asynchronously. The API returns a task ID immediately. |
| **CLI** | Command Line Interface — `python cli.py <command>`. |
| **CORS** | Cross-Origin Resource Sharing — allows a frontend on a different port to call the API. |
| **CV** | Curriculum Vitae — used interchangeably with "resume." |
| **DataFrame** | A pandas 2D table. Used to manage `jobs.csv`. |
| **DRY** | Don't Repeat Yourself. |
| **FastAPI** | A modern Python web framework for building APIs. Provides auto-generated docs, Pydantic integration, and async support. |
| **GPT-4.1-nano** | Cost-efficient OpenAI model for batch scoring. |
| **GPT-4o** | High-capability OpenAI model for document generation. |
| **Interface Layer** | The CLI and API routes. Thin wrappers around the service layer. |
| **Infrastructure Layer** | Modules that handle external I/O: files, APIs, LLMs. |
| **Job ID** | A 6-character alphanumeric identifier (e.g., `ACD123`) for referencing jobs. |
| **LangChain** | Python framework for LLM applications. Manages prompts, parsing, and chains. |
| **LaTeX** | Document preparation system. Pronounced "LAH-tek." |
| **Pydantic** | Python library for data validation using type annotations. Used for API schemas and settings. |
| **Service Layer** | Pure Python functions containing all business logic. Shared by CLI and API. |
| **YAGNI** | You Aren't Gonna Need It. |

<!-- Arch Revision 1 -->

<!-- Arch Revision 2 -->

<!-- Arch Revision 3 -->

<!-- Arch Revision 4 -->

<!-- Arch Revision 5 -->

<!-- Arch Revision 6 -->

<!-- Arch Revision 7 -->

<!-- Arch Revision 8 -->

<!-- Arch Revision 9 -->

<!-- Arch Revision 10 -->

<!-- Arch Revision 11 -->
