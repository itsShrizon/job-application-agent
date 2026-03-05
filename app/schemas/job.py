from typing import Literal
from pydantic import BaseModel, Field


class ScrapeRequest(BaseModel):
    deadline: Literal["24h", "7d", "30d", "anytime"]
    location: str
    role: str | None = None
    work_type: Literal["onsite", "hybrid", "remote"] | None = None
    limit: int = Field(ge=1, le=5000)


class ScrapeContinueRequest(BaseModel):
    new_limit: int = Field(ge=1, le=10000)


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


class JobListResponse(BaseModel):
    total: int
    jobs: list[JobResponse]


class DeadlineReviewResponse(BaseModel):
    expired_count: int
    active_count: int


class ScrapeResultResponse(BaseModel):
    new_count: int
    duplicate_count: int
    total_count: int
