from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.schemas.job import (
    ScrapeRequest, ScrapeContinueRequest, JobResponse, JobListResponse,
    DeadlineReviewResponse, ScrapeResultResponse,
)
from app.schemas.scoring import ScoreResultResponse
from app.schemas.task import TaskResponse
from app.services import job_service, scoring_service
from app.api.deps import create_task, update_task

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


def _run_scrape(task_id: str, req: ScrapeRequest):
    update_task(task_id, status="running")
    try:
        result = job_service.scrape_jobs(
            deadline=req.deadline,
            location=req.location,
            role=req.role,
            work_type=req.work_type,
            limit=req.limit,
        )
        update_task(task_id, status="completed", result=result)
    except Exception as e:
        update_task(task_id, status="failed", error=str(e))


def _run_continue_scrape(task_id: str, new_limit: int):
    update_task(task_id, status="running")
    try:
        result = job_service.continue_scrape(new_limit)
        update_task(task_id, status="completed", result=result)
    except Exception as e:
        update_task(task_id, status="failed", error=str(e))


def _run_scoring(task_id: str):
    update_task(task_id, status="running")
    try:
        result = scoring_service.score_all_unscored()
        result["top_5"] = [_to_job_response(j) for j in result["top_5"]]
        update_task(task_id, status="completed", result=result)
    except Exception as e:
        update_task(task_id, status="failed", error=str(e))


@router.post("/scrape", response_model=TaskResponse)
def api_scrape_jobs(req: ScrapeRequest, bg: BackgroundTasks):
    task_id = create_task()
    bg.add_task(_run_scrape, task_id, req)
    return TaskResponse(task_id=task_id, status="pending", message="Scrape started")


@router.post("/scrape/continue", response_model=TaskResponse)
def api_continue_scrape(req: ScrapeContinueRequest, bg: BackgroundTasks):
    task_id = create_task()
    bg.add_task(_run_continue_scrape, task_id, req.new_limit)
    return TaskResponse(task_id=task_id, status="pending", message="Continue scrape started")


@router.post("/deadline-review", response_model=DeadlineReviewResponse)
def api_deadline_review():
    result = job_service.deadline_review()
    return DeadlineReviewResponse(**result)


@router.post("/score", response_model=TaskResponse)
def api_score_jobs(bg: BackgroundTasks):
    task_id = create_task()
    bg.add_task(_run_scoring, task_id)
    return TaskResponse(task_id=task_id, status="pending", message="Scoring started")


@router.get("/top", response_model=JobListResponse)
def api_top_jobs(limit: int = Query(default=10, ge=1, le=100)):
    jobs = scoring_service.get_top_jobs(limit=limit)
    job_responses = [_to_job_response(j) for j in jobs]
    return JobListResponse(total=len(job_responses), jobs=job_responses)


@router.get("/{job_id}", response_model=JobResponse)
def api_get_job(job_id: str):
    try:
        job = job_service.get_job(job_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail={
            "error_code": "JOB_NOT_FOUND",
            "message": str(e),
            "suggestion": "Run 'python cli.py jobsort' to see available job IDs.",
        })
    return _to_job_response(job)


@router.get("", response_model=JobListResponse)
def api_list_jobs(
    status: str | None = Query(default=None),
    min_score: float | None = Query(default=None),
    sort: str = Query(default="relevance_score"),
    order: str = Query(default="desc"),
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None),
):
    result = job_service.get_jobs(
        status=status,
        min_score=min_score,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
        search=search,
    )
    job_responses = [_to_job_response(j) for j in result["jobs"]]
    return JobListResponse(total=result["total"], jobs=job_responses)


def _to_job_response(job: dict) -> dict:
    score = job.get("relevance_score", "")
    try:
        score = float(score) if score else None
    except (ValueError, TypeError):
        score = None

    cv_gen = str(job.get("cv_generated", "False")).lower() == "true"
    cover_gen = str(job.get("cover_generated", "False")).lower() == "true"

    return {
        "job_id": job.get("job_id", ""),
        "linkedin_id": job.get("linkedin_id", ""),
        "title": job.get("title", ""),
        "company_name": job.get("company_name", ""),
        "company_website": job.get("company_website") or None,
        "location": job.get("location", ""),
        "work_type": job.get("work_type") or None,
        "seniority_level": job.get("seniority_level") or None,
        "employment_type": job.get("employment_type") or None,
        "salary_min": job.get("salary_min") or None,
        "salary_max": job.get("salary_max") or None,
        "description_text": job.get("description_text", ""),
        "posted_at": job.get("posted_at") or None,
        "deadline": job.get("deadline") or None,
        "apply_url": job.get("apply_url") or None,
        "linkedin_url": job.get("linkedin_url", ""),
        "poster_name": job.get("poster_name") or None,
        "poster_title": job.get("poster_title") or None,
        "relevance_score": score,
        "score_reason": job.get("score_reason") or None,
        "status": job.get("status", "new"),
        "cv_generated": cv_gen,
        "cover_generated": cover_gen,
    }
