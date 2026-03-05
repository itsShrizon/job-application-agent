from pydantic import BaseModel


class GitHubRefreshResponse(BaseModel):
    repo_count: int
    file_path: str
