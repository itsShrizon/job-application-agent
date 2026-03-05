import uuid
from threading import Lock

_tasks: dict[str, dict] = {}
_lock = Lock()


def create_task() -> str:
    task_id = str(uuid.uuid4())[:8]
    with _lock:
        _tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "progress": None,
            "result": None,
            "error": None,
        }
    return task_id


def update_task(task_id: str, **kwargs) -> None:
    with _lock:
        if task_id in _tasks:
            _tasks[task_id].update(kwargs)


def get_task(task_id: str) -> dict | None:
    with _lock:
        return _tasks.get(task_id)
