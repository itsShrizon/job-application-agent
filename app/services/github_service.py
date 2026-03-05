import logging

import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


def refresh_github() -> dict:
    if not settings.GITHUB_USERNAME:
        raise ValueError("GITHUB_USERNAME not set in .env")

    headers = {"Authorization": f"token {settings.GITHUB_PAT_TOKEN}"}
    url = f"https://api.github.com/users/{settings.GITHUB_USERNAME}/repos"
    params = {"per_page": 100, "sort": "updated", "direction": "desc"}

    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()

    repos = response.json()
    md_content = _format_repos_md(repos)

    output_path = settings.data_path / "github.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md_content, encoding="utf-8")

    logger.info(f"GitHub refresh: {len(repos)} repos written to {output_path}")
    return {"repo_count": len(repos), "file_path": str(output_path)}


def _format_repos_md(repos: list[dict]) -> str:
    lines = ["# GitHub Projects\n"]

    for repo in repos:
        if repo.get("fork"):
            continue

        name = repo.get("name", "")
        desc = repo.get("description", "") or "No description"
        lang = repo.get("language", "") or "N/A"
        url = repo.get("html_url", "")
        stars = repo.get("stargazers_count", 0)
        topics = ", ".join(repo.get("topics", []))

        lines.append(f"## {name}")
        lines.append(f"- **Description:** {desc}")
        lines.append(f"- **Language:** {lang}")
        lines.append(f"- **Stars:** {stars}")
        if topics:
            lines.append(f"- **Topics:** {topics}")
        lines.append(f"- **URL:** {url}")
        lines.append("")

    return "\n".join(lines)
