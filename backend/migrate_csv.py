"""Run once to migrate existing jobs.csv data to Supabase."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.core.db import init_db
from app.core.csv_manager import append_jobs
import pandas as pd

csv_path = settings.data_path / "jobs.csv"
if not csv_path.exists():
    print("No jobs.csv found, nothing to migrate.")
    sys.exit(0)

init_db()
df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
rows = df.to_dict("records")
added, dupes = append_jobs(rows)
print(f"Migrated: {added} added, {dupes} duplicates skipped")
