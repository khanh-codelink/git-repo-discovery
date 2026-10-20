import asyncio
import uuid

from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from github import Github, GithubException

from src.agents.readme_extraction import ReadmeExtract, extract_readme
from src.agents.repo_report import generate_report, render_report_markdown
from src.auth.github_check import GithubClient
from src.schemas.report_schema import (
    SummaryRequest,
    SummaryResponse,
)
from src.schemas.repository_shema import RepoInput

router = APIRouter()


def _fetch_readme(github_client: Github, repo_id: str) -> ReadmeExtract | None:
    """Fetch and extract a repository's README (blocking). Returns None if unavailable."""
    try:
        readme = github_client.get_repo(int(repo_id)).get_readme()
    except (GithubException, ValueError):
        return None
    return extract_readme(readme.decoded_content.decode("utf-8", errors="replace"))


async def _fetch_readmes(
    github_client: Github, repositories: list[RepoInput]
) -> list[ReadmeExtract | None]:
    return await asyncio.gather(
        *(run_in_threadpool(_fetch_readme, github_client, repo.repo_id) for repo in repositories)
    )


def _missing_readme(
    repositories: list[RepoInput], readmes: list[ReadmeExtract | None]
) -> list[str]:
    return [repo.full_name for repo, readme in zip(repositories, readmes) if readme is None]


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_repositories(request: SummaryRequest, github_client: GithubClient):
    repositories = request.repositories
    readmes = await _fetch_readmes(github_client, repositories)
    report = await generate_report(list(zip(repositories, readmes)))

    return SummaryResponse(
        summary_id=str(uuid.uuid4()),
        summary=render_report_markdown(report),
        selected_repo=repositories[0] if len(repositories) == 1 else None,
        selected_repos=repositories,
        missing_readme=_missing_readme(repositories, readmes),
        report=report,
    )
