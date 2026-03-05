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


class ProfileValidationResponse(BaseModel):
    valid: bool
    errors: list[str]
