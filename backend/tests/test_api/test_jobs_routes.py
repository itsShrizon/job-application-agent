from unittest.mock import patch


@patch("app.api.routes.jobs.job_service")
def test_deadline_review(mock_service, test_client):
    mock_service.deadline_review.return_value = {"expired_count": 3, "active_count": 10}
    resp = test_client.post("/api/jobs/deadline-review")
    assert resp.status_code == 200
    assert resp.json()["expired_count"] == 3


@patch("app.api.routes.jobs.job_service")
def test_get_job_not_found(mock_service, test_client):
    mock_service.get_job.side_effect = KeyError("Job ID 'NOPE' not found")
    resp = test_client.get("/api/jobs/NOPE")
    assert resp.status_code == 404


@patch("app.api.routes.jobs.job_service")
def test_list_jobs(mock_service, test_client):
    mock_service.get_jobs.return_value = {"total": 0, "jobs": []}
    resp = test_client.get("/api/jobs")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
