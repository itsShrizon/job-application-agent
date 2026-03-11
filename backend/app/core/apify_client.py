import time
import logging
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote_plus

from apify_client import ApifyClient

from app.core.config import settings

logger = logging.getLogger(__name__)

ACTOR_ID = "curious_coder~linkedin-jobs-scraper"

# LinkedIn date-posted filter codes
DEADLINE_MAP = {
    "24h": "r86400",    # past 24 hours
    "7d":  "r604800",   # past week
    "30d": "r2592000",  # past month
    "anytime": "",
}

# LinkedIn workplace-type filter codes
WORK_TYPE_MAP = {
    "remote":  "2",
    "hybrid":  "3",
    "onsite":  "1",
}


def _build_linkedin_url(
    role: str | None,
    location: str | None,
    deadline: str | None,
    work_type: str | None,
) -> str:
    """
    Build a LinkedIn Jobs search URL from human-readable parameters.
    LinkedIn's public search URL format:
      https://www.linkedin.com/jobs/search/?keywords=<role>&location=<location>
        &f_TPR=<time_filter>&f_WT=<workplace_filter>
    """
    base = "https://www.linkedin.com/jobs/search/?"
    params: dict[str, str] = {}

    if role:
        params["keywords"] = role
    if location:
        params["location"] = location

    tpr = DEADLINE_MAP.get(deadline or "", "")
    if tpr:
        params["f_TPR"] = tpr

    wt = WORK_TYPE_MAP.get(work_type or "", "")
    if wt:
        params["f_WT"] = wt

    return base + urlencode(params)


def scrape_linkedin_jobs(
    deadline: str,
    location: str,
    role: str | None = None,
    work_type: str | None = None,
    limit: int = 500,
    start_page: int = 0,
) -> list[dict]:
    client = ApifyClient(settings.APIFY_API_TOKEN)

    search_url = _build_linkedin_url(role, location, deadline, work_type)
    logger.info(f"LinkedIn search URL: {search_url}")

    run_input = {
        "urls": [search_url],
        "maxResults": limit,
        "startPage": start_page,
        "proxy": {"useApifyProxy": True},
    }

    logger.info(f"Starting Apify scrape with input: {run_input}")
    run = client.actor(ACTOR_ID).call(run_input=run_input)
    dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items

    logger.info(f"Apify returned {len(dataset_items)} items")
    return [_normalize_item(item) for item in dataset_items]


def _normalize_item(item: dict) -> dict:
    posted_at = item.get("postedAt", "")
    deadline = ""
    if posted_at:
        try:
            posted_dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
            deadline_dt = posted_dt + timedelta(days=settings.DEFAULT_DEADLINE_DAYS)
            deadline = deadline_dt.strftime("%Y-%m-%d")
            posted_at = posted_dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            pass

    return {
        "linkedin_id":             str(item.get("id", "")),
        "title":                   item.get("title", ""),
        "company_name":            item.get("companyName", ""),
        "company_linkedin_url":    item.get("companyLinkedinUrl", ""),
        "company_website":         item.get("companyWebsite", ""),
        "company_logo":            item.get("companyLogo", ""),
        "company_description":     item.get("companyDescription", ""),
        "company_employees_count": str(item.get("companyEmployeesCount", "")),
        "location":                item.get("location", ""),
        "work_type":               _infer_work_type(item),
        "salary_min":              str(item.get("salaryInfo", {}).get("min", "")) if isinstance(item.get("salaryInfo"), dict) else "",
        "salary_max":              str(item.get("salaryInfo", {}).get("max", "")) if isinstance(item.get("salaryInfo"), dict) else "",
        "seniority_level":         item.get("seniorityLevel", ""),
        "employment_type":         item.get("employmentType", ""),
        "job_function":            item.get("jobFunction", ""),
        "industries":              item.get("industries", ""),
        "description_text":        item.get("descriptionText", ""),
        "description_html":        item.get("descriptionHtml", ""),
        "applicants_count":        str(item.get("applicantsCount", "")),
        "posted_at":               posted_at,
        "deadline":                deadline,
        "apply_url":               item.get("applyUrl", ""),
        "linkedin_url":            item.get("link", ""),
        "poster_name":             item.get("jobPosterName", ""),
        "poster_title":            item.get("jobPosterTitle", ""),
        "poster_profile_url":      item.get("jobPosterProfileUrl", ""),
        "relevance_score":         "",
        "score_reason":            "",
        "scraped_at":              datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cv_generated":            "False",
        "cover_generated":         "False",
        "status":                  "new",
    }


def _infer_work_type(item: dict) -> str:
    title    = (item.get("title", "") or "").lower()
    location = (item.get("location", "") or "").lower()
    desc     = (item.get("descriptionText", "") or "").lower()[:500]

    if "remote" in title or "remote" in location:
        return "remote"
    if "hybrid" in title or "hybrid" in location:
        return "hybrid"
    if "remote" in desc:
        return "remote"
    if "hybrid" in desc:
        return "hybrid"
    return "onsite"
