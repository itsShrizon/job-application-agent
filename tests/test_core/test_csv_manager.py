from unittest.mock import patch

import pandas as pd

from app.core.csv_manager import (
    generate_job_id, load_jobs, save_jobs, append_jobs,
    get_job_by_id, update_job, CSV_COLUMNS,
)


def test_generate_job_id():
    jid = generate_job_id("12345")
    assert len(jid) == 6
    assert jid.isalnum()
    assert jid == generate_job_id("12345")


def test_generate_job_id_different_inputs():
    assert generate_job_id("aaa") != generate_job_id("bbb")


def test_load_jobs_no_file(tmp_path):
    with patch("app.core.csv_manager._csv_path", return_value=tmp_path / "jobs.csv"):
        df = load_jobs()
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == CSV_COLUMNS
        assert len(df) == 0


def test_save_and_load_roundtrip(tmp_path):
    csv_path = tmp_path / "jobs.csv"
    with patch("app.core.csv_manager._csv_path", return_value=csv_path):
        df = pd.DataFrame([{"job_id": "ABC123", "title": "Engineer", "linkedin_id": "1"}])
        for col in CSV_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        save_jobs(df)

        loaded = load_jobs()
        assert len(loaded) == 1
        assert loaded.iloc[0]["job_id"] == "ABC123"


def test_append_jobs_deduplication(tmp_path):
    csv_path = tmp_path / "jobs.csv"
    with patch("app.core.csv_manager._csv_path", return_value=csv_path):
        rows = [
            {"linkedin_id": "111", "title": "Dev"},
            {"linkedin_id": "222", "title": "PM"},
            {"linkedin_id": "111", "title": "Dev Dup"},
        ]
        added, dups = append_jobs(rows)
        assert added == 2
        assert dups == 1


def test_get_job_by_id(tmp_path):
    csv_path = tmp_path / "jobs.csv"
    with patch("app.core.csv_manager._csv_path", return_value=csv_path):
        append_jobs([{"linkedin_id": "999", "title": "Tester"}])
        df = load_jobs()
        job_id = df.iloc[0]["job_id"]

        job = get_job_by_id(job_id)
        assert job["title"] == "Tester"


def test_get_job_by_id_not_found(tmp_path):
    csv_path = tmp_path / "jobs.csv"
    with patch("app.core.csv_manager._csv_path", return_value=csv_path):
        try:
            get_job_by_id("NONEXIST")
            assert False, "Should have raised KeyError"
        except KeyError:
            pass


def test_update_job(tmp_path):
    csv_path = tmp_path / "jobs.csv"
    with patch("app.core.csv_manager._csv_path", return_value=csv_path):
        append_jobs([{"linkedin_id": "555", "title": "Old Title"}])
        df = load_jobs()
        job_id = df.iloc[0]["job_id"]

        update_job(job_id, {"title": "New Title"})

        job = get_job_by_id(job_id)
        assert job["title"] == "New Title"
