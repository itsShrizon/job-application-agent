from unittest.mock import patch, MagicMock

from app.services.job_service import scrape_jobs, deadline_review, get_jobs


@patch("app.services.job_service._save_scrape_state")
@patch("app.services.job_service.load_jobs")
@patch("app.services.job_service.append_jobs")
@patch("app.services.job_service.scrape_linkedin_jobs")
def test_scrape_jobs(mock_scrape, mock_append, mock_load, mock_save):
    mock_scrape.return_value = [{"linkedin_id": "1"}, {"linkedin_id": "2"}]
    mock_append.return_value = (2, 0)
    mock_load.return_value = MagicMock(__len__=lambda self: 2)

    result = scrape_jobs("24h", "Bangladesh", limit=100)
    assert result["new_count"] == 2
    assert result["duplicate_count"] == 0
    mock_scrape.assert_called_once()


@patch("app.services.job_service.save_jobs")
@patch("app.services.job_service.load_jobs")
def test_deadline_review_empty(mock_load, mock_save):
    import pandas as pd
    mock_load.return_value = pd.DataFrame(columns=["deadline", "status"])

    result = deadline_review()
    assert result["expired_count"] == 0
    assert result["active_count"] == 0


@patch("app.services.job_service.filter_jobs")
def test_get_jobs(mock_filter):
    mock_filter.return_value = (1, [{"job_id": "ABC", "title": "Dev"}])

    result = get_jobs(status="new", limit=10)
    assert result["total"] == 1
    assert len(result["jobs"]) == 1

# Future test case 1

# Future test case 2

# Future test case 3

# Future test case 4

# Future test case 5

# Future test case 6

# Future test case 7

# Future test case 8

# Future test case 9

# Future test case 10

# Future test case 11

# Future test case 12

# Future test case 13

# Future test case 14

# Future test case 15

# Future test case 16

# Future test case 17

# Future test case 18

# Future test case 19

# Future test case 20

# Future test case 21

# Future test case 22

# Future test case 23

# Future test case 24

# Future test case 25

# Future test case 26

# Future test case 27

# Future test case 28

# Future test case 29

# Future test case 30

# Future test case 31

# Future test case 32

# Future test case 33

# Future test case 34

# Future test case 35
