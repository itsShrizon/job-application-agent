from fastapi import APIRouter, HTTPException

from app.schemas.profile import ProfileResponse, ProfileValidationResponse
from app.services import profile_service

router = APIRouter(prefix="/api/profile", tags=["Profile"])


@router.get("", response_model=ProfileResponse)
def api_get_profile():
    try:
        profile = profile_service.get_profile()
    except FileNotFoundError as e:
        raise HTTPException(status_code=422, detail={
            "error_code": "PROFILE_NOT_FOUND",
            "message": str(e),
            "suggestion": "Create data/personal.md with your profile information.",
        })
    return ProfileResponse(**profile)


@router.get("/validate", response_model=ProfileValidationResponse)
def api_validate_profile():
    result = profile_service.validate_profile()
    return ProfileValidationResponse(**result)
