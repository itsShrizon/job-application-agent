from pydantic import BaseModel

from app.schemas.job import JobResponse


class ScoreResultResponse(BaseModel):
    scored_count: int
    top_5: list[JobResponse]
