from typing import Literal
from pydantic import BaseModel


class TaskResponse(BaseModel):
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    message: str | None = None


class TaskStatusResponse(BaseModel):
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    progress: float | None = None
    result: dict | None = None
    error: str | None = None
