from typing import Literal
from pydantic import BaseModel, model_validator


class CVGenerateRequest(BaseModel):
    job_id: str | None = None
    job_file: str | None = None
    template: Literal["t1", "t2", "t3"]

    @model_validator(mode="after")
    def check_job_reference(self):
        if not self.job_id and not self.job_file:
            raise ValueError("Provide either job_id or job_file")
        if self.job_id and self.job_file:
            raise ValueError("Provide only one of job_id or job_file")
        return self


class CustomCVGenerateRequest(BaseModel):
    title: str
    company_name: str
    description: str
    template: Literal["t1", "t2", "t3"]


class CVGenerateResponse(BaseModel):
    pdf_path: str
    job_id: str
    job_title: str
    company_name: str
    template_used: str
