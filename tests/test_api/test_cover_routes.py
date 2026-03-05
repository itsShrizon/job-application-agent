from unittest.mock import patch


@patch("app.api.routes.cover.cover_service")
def test_generate_cover_missing_ref(mock_service, test_client):
    resp = test_client.post("/api/cover/generate", json={})
    assert resp.status_code == 422


@patch("app.api.routes.cover.cover_service")
def test_generate_cover_success(mock_service, test_client):
    mock_service.generate_cover.return_value = {
        "pdf_path": "/output/cover/test.pdf",
        "job_id": "XYZ789",
        "job_title": "Analyst",
        "company_name": "DataCo",
    }
    resp = test_client.post("/api/cover/generate", json={"job_id": "XYZ789"})
    assert resp.status_code == 200
    assert resp.json()["company_name"] == "DataCo"
