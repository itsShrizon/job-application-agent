from fastapi import APIRouter, HTTPException

from app.schemas.github import GitHubRefreshResponse
from app.services import github_service

router = APIRouter(prefix="/api/github", tags=["GitHub"])


@router.post("/refresh", response_model=GitHubRefreshResponse)
def api_refresh_github():
    try:
        result = github_service.refresh_github()
    except ValueError as e:
        raise HTTPException(status_code=422, detail={
            "error_code": "CONFIG_ERROR",
            "message": str(e),
        })
    except Exception as e:
        raise HTTPException(status_code=502, detail={
            "error_code": "GITHUB_API_ERROR",
            "message": str(e),
            "suggestion": "Check GITHUB_PAT_TOKEN and GITHUB_USERNAME in .env.",
        })
    return GitHubRefreshResponse(**result)
