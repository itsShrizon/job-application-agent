from pydantic import BaseModel, model_validator


class CoverGenerateRequest(BaseModel):
    job_id: str | None = None
    job_file: str | None = None

    @model_validator(mode="after")
    def check_job_reference(self):
        if not self.job_id and not self.job_file:
            raise ValueError("Provide either job_id or job_file")
        if self.job_id and self.job_file:
            raise ValueError("Provide only one of job_id or job_file")
        return self


class CoverGenerateResponse(BaseModel):
    pdf_path: str
    job_id: str
    job_title: str
    company_name: str
