import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings

logger = logging.getLogger(__name__)

_conn = None

def get_conn():
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(settings.DATABASE_URL, cursor_factory=RealDictCursor)
        _conn.autocommit = True
    return _conn

def execute(sql: str, params=None):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(sql, params)

def fetchall(sql: str, params=None) -> list[dict]:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]

def fetchone(sql: str, params=None) -> dict | None:
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None

def init_db():
    execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id VARCHAR(20) PRIMARY KEY,
            linkedin_id TEXT UNIQUE,
            title TEXT DEFAULT '',
            company_name TEXT DEFAULT '',
            company_linkedin_url TEXT DEFAULT '',
            company_website TEXT DEFAULT '',
            company_logo TEXT DEFAULT '',
            company_description TEXT DEFAULT '',
            company_employees_count TEXT DEFAULT '',
            location TEXT DEFAULT '',
            work_type TEXT DEFAULT '',
            salary_min TEXT DEFAULT '',
            salary_max TEXT DEFAULT '',
            seniority_level TEXT DEFAULT '',
            employment_type TEXT DEFAULT '',
            job_function TEXT DEFAULT '',
            industries TEXT DEFAULT '',
            description_text TEXT DEFAULT '',
            description_html TEXT DEFAULT '',
            applicants_count TEXT DEFAULT '',
            posted_at TEXT DEFAULT '',
            deadline TEXT DEFAULT '',
            apply_url TEXT DEFAULT '',
            linkedin_url TEXT DEFAULT '',
            poster_name TEXT DEFAULT '',
            poster_title TEXT DEFAULT '',
            poster_profile_url TEXT DEFAULT '',
            relevance_score FLOAT,
            score_reason TEXT DEFAULT '',
            scraped_at TEXT DEFAULT '',
            cv_generated BOOLEAN DEFAULT FALSE,
            cover_generated BOOLEAN DEFAULT FALSE,
            status TEXT DEFAULT 'new'
        )
    """)
    logger.info("Database initialized")
