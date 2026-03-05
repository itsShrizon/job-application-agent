from fastapi import APIRouter, HTTPException

from app.schemas.task import TaskStatusResponse
from app.api.deps import get_task

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


@router.get("/{task_id}", response_model=TaskStatusResponse)
def api_get_task_status(task_id: str):
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail={
            "error_code": "TASK_NOT_FOUND",
            "message": f"Task '{task_id}' not found.",
        })
    return TaskStatusResponse(**task)
