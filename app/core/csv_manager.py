import hashlib
from pathlib import Path

import pandas as pd

from app.core.config import settings

CSV_COLUMNS = [
    "job_id", "linkedin_id", "title", "company_name", "company_linkedin_url",
    "company_website", "company_logo", "company_description", "company_employees_count",
    "location", "work_type", "salary_min", "salary_max", "seniority_level",
    "employment_type", "job_function", "industries", "description_text",
    "description_html", "applicants_count", "posted_at", "deadline", "apply_url",
    "linkedin_url", "poster_name", "poster_title", "poster_profile_url",
    "relevance_score", "score_reason", "scraped_at", "cv_generated",
    "cover_generated", "status",
]


def _csv_path() -> Path:
    return settings.data_path / "jobs.csv"


def generate_job_id(linkedin_id: str) -> str:
    return hashlib.md5(linkedin_id.encode()).hexdigest()[:6].upper()


def load_jobs() -> pd.DataFrame:
    path = _csv_path()
    if not path.exists():
        return pd.DataFrame(columns=CSV_COLUMNS)
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    for col in CSV_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df


def save_jobs(df: pd.DataFrame) -> None:
    path = _csv_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def append_jobs(new_rows: list[dict]) -> tuple[int, int]:
    df = load_jobs()
    existing_ids = set(df["linkedin_id"].tolist())

    added = 0
    duplicates = 0
    for row in new_rows:
        lid = str(row.get("linkedin_id", ""))
        if lid in existing_ids:
            duplicates += 1
            continue

        job_id = generate_job_id(lid)
        if job_id in set(df["job_id"].tolist()):
            job_id = f"{job_id}-2"

        row["job_id"] = job_id
        for col in CSV_COLUMNS:
            row.setdefault(col, "")

        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        existing_ids.add(lid)
        added += 1

    save_jobs(df)
    return added, duplicates


def get_job_by_id(job_id: str) -> dict:
    df = load_jobs()
    matches = df[df["job_id"] == job_id]
    if matches.empty:
        raise KeyError(f"Job ID '{job_id}' not found in jobs.csv.")
    return matches.iloc[0].to_dict()


def update_job(job_id: str, updates: dict) -> None:
    df = load_jobs()
    mask = df["job_id"] == job_id
    if not mask.any():
        raise KeyError(f"Job ID '{job_id}' not found in jobs.csv.")
    for key, value in updates.items():
        if key in df.columns:
            df.loc[mask, key] = value
    save_jobs(df)


def get_unscored_jobs() -> pd.DataFrame:
    df = load_jobs()
    return df[(df["relevance_score"] == "") & (df["status"] != "expired")]


def get_scored_jobs(limit: int = 50) -> pd.DataFrame:
    df = load_jobs()
    scored = df[df["relevance_score"] != ""].copy()
    scored["relevance_score"] = pd.to_numeric(scored["relevance_score"], errors="coerce")
    return scored.sort_values("relevance_score", ascending=False).head(limit)


def filter_jobs(
    status: str | None = None,
    min_score: float | None = None,
    sort: str = "relevance_score",
    order: str = "desc",
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
) -> tuple[int, list[dict]]:
    df = load_jobs()

    if status:
        df = df[df["status"] == status]

    if min_score is not None:
        df["_score"] = pd.to_numeric(df["relevance_score"], errors="coerce")
        df = df[df["_score"] >= min_score]
        df = df.drop(columns=["_score"])

    if search:
        term = search.lower()
        mask = (
            df["title"].str.lower().str.contains(term, na=False)
            | df["company_name"].str.lower().str.contains(term, na=False)
            | df["description_text"].str.lower().str.contains(term, na=False)
        )
        df = df[mask]

    total = len(df)

    if sort in df.columns:
        if sort == "relevance_score":
            df["_sort"] = pd.to_numeric(df["relevance_score"], errors="coerce")
            df = df.sort_values("_sort", ascending=(order == "asc"), na_position="last")
            df = df.drop(columns=["_sort"])
        else:
            df = df.sort_values(sort, ascending=(order == "asc"))

    df = df.iloc[offset : offset + limit]
    return total, df.to_dict("records")
