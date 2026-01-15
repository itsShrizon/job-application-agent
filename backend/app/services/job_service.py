import json
import typing
import logging
from datetime import datetime, date

from app.core.config import settings
from app.core.apify_client import scrape_linkedin_jobs
from app.core.csv_manager import (
    append_jobs, get_job_by_id, filter_jobs,
    mark_expired_jobs,
)
from app.core.db import fetchone

logger = logging.getLogger(__name__)

SCRAPE_STATE_FILE = settings.data_path / "scrape_state" / "last_run.json"


def scrape_jobs(
    """
    Scrapes LinkedIn jobs based on the provided search criteria.
    """
    deadline: str,
    location: str,
    role: str | None = None,
    work_type: str | None = None,
    limit: int = 500,
) -> dict:
    raw_jobs = scrape_linkedin_jobs(
        deadline=deadline,
        location=location,
        role=role,
        work_type=work_type,
        limit=limit,
    )

    added, duplicates = append_jobs(raw_jobs)
    total_row = fetchone("SELECT COUNT(*) as cnt FROM jobs")
    total = total_row["cnt"] if total_row else 0

    _save_scrape_state({
        "deadline": deadline,
        "location": location,
        "role": role,
        "work_type": work_type,
        "limit": limit,
        "results_fetched": len(raw_jobs),
        "timestamp": datetime.now().isoformat(),
    })

    logger.info(f"Scrape complete: {added} new, {duplicates} duplicates, {total} total")
    return {"new_count": added, "duplicate_count": duplicates, "total_count": total}


def continue_scrape(
    """
    Continues a previous scrape session using stored state.
    """
    state = _load_scrape_state()
    if not state:
        raise FileNotFoundError("No previous scrape found. Run jobfind first.")

    prev_limit = state.get("limit", 0)
    if new_limit <= prev_limit:
        raise ValueError(f"new_limit ({new_limit}) must be greater than previous limit ({prev_limit})")

    raw_jobs = scrape_linkedin_jobs(
        deadline=state["deadline"],
        location=state["location"],
        role=state.get("role"),
        work_type=state.get("work_type"),
        limit=new_limit,
        start_page=state.get("results_fetched", 0),
    )

    added, duplicates = append_jobs(raw_jobs)
    total_row = fetchone("SELECT COUNT(*) as cnt FROM jobs")
    total = total_row["cnt"] if total_row else 0

    state["limit"] = new_limit
    state["results_fetched"] = state.get("results_fetched", 0) + len(raw_jobs)
    state["timestamp"] = datetime.now().isoformat()
    _save_scrape_state(state)

    return {"new_count": added, "duplicate_count": duplicates, "total_count": total}


def deadline_review() -> dict:
    today = date.today().isoformat()
    expired_total, active_count = mark_expired_jobs(today)
    logger.info(f"Deadline review: active={active_count}")
    return {"expired_count": expired_total, "active_count": active_count}


def get_jobs(
    status: str | None = None,
    min_score: float | None = None,
    sort: str = "relevance_score",
    order: str = "desc",
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
) -> dict:
    total, jobs = filter_jobs(
        status=status,
        min_score=min_score,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
        search=search,
    )
    return {"total": total, "jobs": jobs}


def get_job(job_id: str) -> dict:
    return get_job_by_id(job_id)


def delete_job(job_id: str) -> bool:
    from app.core.csv_manager import delete_job_by_id
    return delete_job_by_id(job_id)


def delete_all_jobs() -> int:
    from app.core.csv_manager import delete_all_jobs as db_delete_all
    return db_delete_all()


def _save_scrape_state(state: dict) -> None:
    SCRAPE_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SCRAPE_STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _load_scrape_state() -> dict | None:
    if not SCRAPE_STATE_FILE.exists():
        return None
    return json.loads(SCRAPE_STATE_FILE.read_text(encoding="utf-8"))
