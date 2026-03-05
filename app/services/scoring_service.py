import logging

from app.core.csv_manager import get_unscored_jobs, load_jobs, save_jobs, get_scored_jobs
from app.core.parser import read_personal_md
from app.core.llm_chains import invoke_scoring_chain

logger = logging.getLogger(__name__)

BATCH_SIZE = 10


def score_all_unscored() -> dict:
    profile = read_personal_md()
    candidate_summary = _build_candidate_summary(profile)

    unscored = get_unscored_jobs()
    if unscored.empty:
        return {"scored_count": 0, "top_5": []}

    df = load_jobs()
    scored_count = 0

    for i in range(0, len(unscored), BATCH_SIZE):
        batch = unscored.iloc[i : i + BATCH_SIZE]
        jobs_text = _format_jobs_batch(batch)

        try:
            results = invoke_scoring_chain(candidate_summary, jobs_text)
        except Exception as e:
            logger.warning(f"Scoring batch failed: {e}")
            continue

        for result in results:
            idx = result.get("job_index")
            if idx is None or idx >= len(batch):
                continue

            job_id = batch.iloc[idx]["job_id"]
            mask = df["job_id"] == job_id
            df.loc[mask, "relevance_score"] = str(result.get("score", 0))
            df.loc[mask, "score_reason"] = str(result.get("reason", ""))
            df.loc[mask, "status"] = "scored"
            scored_count += 1

    save_jobs(df)

    top_5 = get_scored_jobs(limit=5).to_dict("records")
    logger.info(f"Scored {scored_count} jobs")
    return {"scored_count": scored_count, "top_5": top_5}


def rescore_all() -> dict:
    df = load_jobs()
    df["relevance_score"] = ""
    df["score_reason"] = ""
    df.loc[df["status"] == "scored", "status"] = "new"
    save_jobs(df)
    return score_all_unscored()


def get_top_jobs(limit: int = 10) -> list[dict]:
    return get_scored_jobs(limit=limit).to_dict("records")


def _build_candidate_summary(profile: dict) -> str:
    parts = []
    if profile.get("name"):
        parts.append(f"Name: {profile['name']}")
    if profile.get("skills"):
        parts.append(f"Skills: {profile['skills']}")
    if profile.get("experience"):
        parts.append(f"Experience: {profile['experience'][:500]}")
    if profile.get("education"):
        parts.append(f"Education: {profile['education'][:200]}")
    return "\n".join(parts)


def _format_jobs_batch(batch) -> str:
    lines = []
    for idx, (_, row) in enumerate(batch.iterrows()):
        desc = (row.get("description_text", "") or "")[:800]
        if not desc.strip():
            continue
        lines.append(
            f"[Job {idx}]\n"
            f"Title: {row.get('title', '')}\n"
            f"Company: {row.get('company_name', '')}\n"
            f"Location: {row.get('location', '')}\n"
            f"Seniority: {row.get('seniority_level', '')}\n"
            f"Description: {desc}\n"
        )
    return "\n".join(lines)
