from unittest.mock import patch


@patch("app.api.routes.cv.cv_service")
def test_generate_cv_missing_ref(mock_service, test_client):
    resp = test_client.post("/api/cv/generate", json={"template": "t1"})
    assert resp.status_code == 422


@patch("app.api.routes.cv.cv_service")
def test_generate_cv_both_refs(mock_service, test_client):
    resp = test_client.post("/api/cv/generate", json={
        "job_id": "ABC",
        "job_file": "test.md",
        "template": "t1",
    })
    assert resp.status_code == 422


@patch("app.api.routes.cv.cv_service")
def test_generate_cv_success(mock_service, test_client):
    mock_service.generate_cv.return_value = {
        "pdf_path": "/output/cv/test.pdf",
        "job_id": "ABC123",
        "job_title": "Engineer",
        "company_name": "Corp",
        "template_used": "t1",
    }
    resp = test_client.post("/api/cv/generate", json={
        "job_id": "ABC123",
        "template": "t1",
    })
    assert resp.status_code == 200
    assert resp.json()["job_title"] == "Engineer"
