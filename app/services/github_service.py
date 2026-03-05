import base64
import logging

import requests
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.config import settings

logger = logging.getLogger(__name__)

# Source file extensions to read when there's no README
_CODE_EXTENSIONS = {".py", ".js", ".ts", ".go", ".rs", ".java", ".cpp", ".c", ".cs", ".rb"}
# Max chars of README / file content to send to the LLM
_MAX_CONTENT_CHARS = 3000


def refresh_github() -> dict:
    if not settings.GITHUB_USERNAME:
        raise ValueError("GITHUB_USERNAME not set in .env")

    headers = {
        "Authorization": f"token {settings.GITHUB_PAT_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    url = f"https://api.github.com/users/{settings.GITHUB_USERNAME}/repos"
    params = {"per_page": 100, "sort": "updated", "direction": "desc"}

    response = requests.get(url, headers=headers, params=params, timeout=30)
    response.raise_for_status()
    repos = response.json()

    enriched = 0
    for repo in repos:
        if repo.get("fork"):
            continue
        if not repo.get("description"):
            desc = _generate_description(repo, headers)
            if desc:
                repo["description"] = desc
                enriched += 1
                logger.info(f"[gitref] AI description generated for: {repo['name']}")

    md_content = _format_repos_md(repos)
    output_path = settings.data_path / "github.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md_content, encoding="utf-8")

    logger.info(
        f"GitHub refresh: {len(repos)} repos written to {output_path} "
        f"({enriched} descriptions AI-generated)"
    )
    return {
        "repo_count": len(repos),
        "ai_enriched": enriched,
        "file_path": str(output_path),
    }


# ── AI enrichment ──────────────────────────────────────────────────────────────

def _generate_description(repo: dict, headers: dict) -> str:
    """Try README first, then source files, then give up."""
    name = repo.get("name", "")
    context = _fetch_readme(name, headers) or _fetch_source_snippet(repo, headers)
    if not context:
        logger.warning(f"[gitref] No context found for {name}, skipping AI description.")
        return ""
    return _ask_openai(name, context)


def _fetch_readme(repo_name: str, headers: dict) -> str:
    """Fetch and decode README.md via GitHub API. Returns plain text or ''."""
    url = f"https://api.github.com/repos/{settings.GITHUB_USERNAME}/{repo_name}/readme"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 404:
            return ""
        r.raise_for_status()
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return content[:_MAX_CONTENT_CHARS]
    except Exception as e:
        logger.debug(f"[gitref] README fetch failed for {repo_name}: {e}")
        return ""


def _fetch_source_snippet(repo: dict, headers: dict) -> str:
    """
    When there's no README, fetch the repo's file tree and read
    the first 1–3 source files to give OpenAI enough context.
    """
    name = repo.get("name", "")
    default_branch = repo.get("default_branch", "main")

    tree_url = (
        f"https://api.github.com/repos/{settings.GITHUB_USERNAME}/{name}"
        f"/git/trees/{default_branch}?recursive=1"
    )
    try:
        r = requests.get(tree_url, headers=headers, timeout=15)
        if r.status_code != 200:
            return ""
        tree = r.json().get("tree", [])
    except Exception as e:
        logger.debug(f"[gitref] Tree fetch failed for {name}: {e}")
        return ""

    # Pick up to 3 source files (prefer root-level files)
    candidates = [
        item for item in tree
        if item.get("type") == "blob"
        and any(item["path"].endswith(ext) for ext in _CODE_EXTENSIONS)
        and "/" not in item["path"]  # root-level first
    ]
    if not candidates:
        # Fall back to any source file anywhere in the repo
        candidates = [
            item for item in tree
            if item.get("type") == "blob"
            and any(item["path"].endswith(ext) for ext in _CODE_EXTENSIONS)
        ]

    snippets = []
    chars_used = 0
    for item in candidates[:3]:
        if chars_used >= _MAX_CONTENT_CHARS:
            break
        content = _fetch_file_content(name, item["path"], headers)
        if content:
            snippet = f"--- {item['path']} ---\n{content}"
            remaining = _MAX_CONTENT_CHARS - chars_used
            snippets.append(snippet[:remaining])
            chars_used += len(snippet)

    return "\n\n".join(snippets)


def _fetch_file_content(repo_name: str, path: str, headers: dict) -> str:
    url = f"https://api.github.com/repos/{settings.GITHUB_USERNAME}/{repo_name}/contents/{path}"
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return ""
        data = r.json()
        raw = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        return raw[:1500]
    except Exception as e:
        logger.debug(f"[gitref] File fetch failed ({repo_name}/{path}): {e}")
        return ""


def _ask_openai(repo_name: str, context: str) -> str:
    """Call GPT-4o-mini to generate a 1–2 sentence repo description."""
    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=100,
            api_key=settings.OPENAI_API_KEY,
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are a technical writer. Given a GitHub repository name and its content, "
             "write a single concise sentence (max 20 words) that describes what the project does. "
             "Return ONLY the description sentence, nothing else."),
            ("human",
             "Repository: {repo_name}\n\nContent:\n{context}\n\nDescription:"),
        ])
        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"repo_name": repo_name, "context": context})
        return result.strip().strip('"').strip("'")
    except Exception as e:
        logger.warning(f"[gitref] OpenAI call failed for {repo_name}: {e}")
        return ""


# ── Formatting ─────────────────────────────────────────────────────────────────

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
