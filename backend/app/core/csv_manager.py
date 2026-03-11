import hashlib
import logging

from app.core.db import fetchall, fetchone, execute

logger = logging.getLogger(__name__)

DB_COLUMNS = [
    "job_id", "linkedin_id", "title", "company_name", "company_linkedin_url",
    "company_website", "company_logo", "company_description", "company_employees_count",
    "location", "work_type", "salary_min", "salary_max", "seniority_level",
    "employment_type", "job_function", "industries", "description_text",
    "description_html", "applicants_count", "posted_at", "deadline", "apply_url",
    "linkedin_url", "poster_name", "poster_title", "poster_profile_url",
    "relevance_score", "score_reason", "scraped_at", "cv_generated",
    "cover_generated", "status",
]


def generate_job_id(linkedin_id: str) -> str:
    return hashlib.md5(linkedin_id.encode()).hexdigest()[:6].upper()


def load_jobs() -> list[dict]:
    return fetchall("SELECT * FROM jobs ORDER BY scraped_at DESC")


def save_jobs(_) -> None:
    pass  # no-op — direct DB writes are used instead


def append_jobs(new_rows: list[dict]) -> tuple[int, int]:
    added = 0
    duplicates = 0

    existing = {row["linkedin_id"] for row in fetchall("SELECT linkedin_id FROM jobs")}
    existing_ids = {row["job_id"] for row in fetchall("SELECT job_id FROM jobs")}

    for row in new_rows:
        lid = str(row.get("linkedin_id", ""))
        if lid in existing:
            duplicates += 1
            continue

        job_id = generate_job_id(lid)
        if job_id in existing_ids:
            job_id = f"{job_id}-2"

        row["job_id"] = job_id

        insert_data = {c: row.get(c, "") for c in DB_COLUMNS}
        insert_data["job_id"] = job_id
        insert_data["linkedin_id"] = lid

        # Handle boolean and numeric fields
        insert_data["cv_generated"] = bool(insert_data.get("cv_generated", False))
        insert_data["cover_generated"] = bool(insert_data.get("cover_generated", False))
        score = insert_data.get("relevance_score", "")
        insert_data["relevance_score"] = float(score) if score and score != "" else None

        col_names = list(insert_data.keys())
        placeholders = ", ".join(["%s"] * len(col_names))
        col_str = ", ".join(col_names)
        values = [insert_data[c] for c in col_names]

        execute(
            f"INSERT INTO jobs ({col_str}) VALUES ({placeholders}) ON CONFLICT (linkedin_id) DO NOTHING",
            values,
        )
        existing.add(lid)
        existing_ids.add(job_id)
        added += 1

    return added, duplicates


def get_job_by_id(job_id: str) -> dict:
    row = fetchone("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
    if not row:
        raise KeyError(f"Job ID '{job_id}' not found.")
    return row


def update_job(job_id: str, updates: dict) -> None:
    if not updates:
        return

    # Handle boolean coercion
    if "cv_generated" in updates:
        updates["cv_generated"] = updates["cv_generated"] in (True, "True", "true", 1)
    if "cover_generated" in updates:
        updates["cover_generated"] = updates["cover_generated"] in (True, "True", "true", 1)

    set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
    values = list(updates.values()) + [job_id]
    execute(f"UPDATE jobs SET {set_clause} WHERE job_id = %s", values)


def get_unscored_jobs() -> list[dict]:
    return fetchall("SELECT * FROM jobs WHERE relevance_score IS NULL AND status != 'expired'")


def get_scored_jobs(limit: int = 50) -> list[dict]:
    return fetchall(
        "SELECT * FROM jobs WHERE relevance_score IS NOT NULL ORDER BY relevance_score DESC LIMIT %s",
        (limit,),
    )


def mark_expired_jobs(today_str: str) -> tuple[int, int]:
    execute(
        "UPDATE jobs SET status = 'expired' WHERE deadline != '' AND deadline < %s AND status != 'expired'",
        (today_str,),
    )
    row = fetchone("SELECT COUNT(*) as cnt FROM jobs WHERE status != 'expired'")
    active_count = row["cnt"] if row else 0
    expired_row = fetchone("SELECT COUNT(*) as cnt FROM jobs WHERE status = 'expired'")
    expired_total = expired_row["cnt"] if expired_row else 0
    return expired_total, active_count


def filter_jobs(
    status: str | None = None,
    min_score: float | None = None,
    sort: str = "relevance_score",
    order: str = "desc",
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
) -> tuple[int, list[dict]]:
    conditions = []
    params = []

    if status:
        conditions.append("status = %s")
        params.append(status)

    if min_score is not None:
        conditions.append("relevance_score >= %s")
        params.append(min_score)

    if search:
        conditions.append("(LOWER(title) LIKE %s OR LOWER(company_name) LIKE %s OR LOWER(description_text) LIKE %s)")
        term = f"%{search.lower()}%"
        params.extend([term, term, term])

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    # Safe column whitelist
    allowed_sort = {
        "relevance_score", "title", "company_name", "scraped_at", "deadline", "status", "posted_at"
    }
    sort_col = sort if sort in allowed_sort else "relevance_score"
    sort_dir = "ASC" if order == "asc" else "DESC"
    null_pos = "NULLS LAST" if sort_dir == "DESC" else "NULLS FIRST"

    count_row = fetchone(f"SELECT COUNT(*) as cnt FROM jobs {where}", params or None)
    total = count_row["cnt"] if count_row else 0

    rows = fetchall(
        f"SELECT * FROM jobs {where} ORDER BY {sort_col} {sort_dir} {null_pos} LIMIT %s OFFSET %s",
        (params + [limit, offset]) or [limit, offset],
    )
    return total, rows
