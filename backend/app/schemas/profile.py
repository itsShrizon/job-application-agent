from pydantic import BaseModel


class ProfileResponse(BaseModel):
    name: str
    email: str
    phone: str
    linkedin: str
    github: str
    location: str
    portfolio: str
    skills: str
    experience: str
    education: str
    certifications: str
    summary: str
    achievements: str


class ProfileUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    location: str | None = None
    portfolio: str | None = None
    skills: str | None = None
    experience: str | None = None
    education: str | None = None
    certifications: str | None = None
    summary: str | None = None
    achievements: str | None = None


class ProfileValidationResponse(BaseModel):
    valid: bool
    errors: list[str]
