import asyncio
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.concurrency import run_in_threadpool
from github import Github, GithubException

from src.agents.readme_extraction import ReadmeExtract, extract_readme
from src.agents.repo_report import generate_report, render_report_markdown
from src.auth.dependencies import AuthContext, get_auth_context
from src.auth.github_check import GithubClient
from src.schemas.report_schema import ComparisonResponse, RepositoriesRequest, SummaryResponse
from src.schemas.repository_shema import RepoInput
from src.services.observability import observe, propagate_attributes, record_input
from src.shared.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@observe(name="fetch README", as_type="tool", capture_input=False)
def _fetch_readme(github_client: Github, repo_id: str) -> ReadmeExtract | None:
    """Fetch and extract a repository's README (blocking). Returns None if unavailable."""
    record_input(repo_id=repo_id)
    try:
        readme = github_client.get_repo(int(repo_id)).get_readme()
    except (GithubException, ValueError) as e:
        logger.warning("No README for repo %s (%s)", repo_id, type(e).__name__)
        return None
    return extract_readme(readme.decoded_content.decode("utf-8", errors="replace"))


@observe(name="README fetch + cleaning", capture_input=False)
async def _fetch_readmes(
    github_client: Github,
    repositories: list[RepoInput],
    mode: Literal["summary", "compare"] = "summary",
) -> list[ReadmeExtract | None]:
    record_input(repositories=[repo.full_name for repo in repositories], mode=mode)
    if mode == "compare":
        if len(repositories) <= 1:
            raise Exception("Compare mode should have more than 1 repo selected.")
        else:
            return await asyncio.gather(
                *(
                    run_in_threadpool(_fetch_readme, github_client, repo.repo_id)
                    for repo in repositories
                )
            )
    elif mode == "summary":
        return [await run_in_threadpool(_fetch_readme, github_client, repositories[0].repo_id)]
    else:
        raise ValueError("No mode found for _fetch_readmes")


def _missing_readme(
    repositories: list[RepoInput], readmes: list[ReadmeExtract | None]
) -> list[str]:
    return [repo.full_name for repo, readme in zip(repositories, readmes) if readme is None]


@router.post("/summarize", response_model=SummaryResponse)
@observe(name="Summary pipeline", capture_input=False)
async def summarize_repositories(
    request: RepositoriesRequest,
    github_client: GithubClient,
    context: AuthContext = Depends(get_auth_context),
):
    user_id = context.user_id
    db = context.client

    assert user_id is not None

    repositories = request.repositories[:1]
    logger.info("Summarizing %s for user %s", repositories[0].full_name, user_id)
    record_input(repositories=[repo.full_name for repo in repositories])
    with propagate_attributes(
        user_id=str(user_id), metadata={"mode": "summary", "repo_count": len(repositories)}
    ):
        readme = await _fetch_readmes(github_client, repositories, "summary")
        report = await generate_report(list(zip(repositories, readme, strict=True)), "summary")

    response = SummaryResponse(
        summary_id=str(uuid.uuid4()),
        summary=render_report_markdown(report),
        selected_repo=repositories[0] if len(repositories) == 1 else None,
        missing_readme=_missing_readme(repositories, readme),
        report=report,
        report_type="summary",
    )
    # Columns mirror SummaryResponse; the LLM report is stored whole in the `report` jsonb column.
    db.table("summaries").insert(
        {**response.model_dump(mode="json"), "user_id": str(user_id)}
    ).execute()
    logger.info("Saved summary %s", response.summary_id)
    return response


@router.post("/compare", response_model=ComparisonResponse)
@observe(name="Comparison pipeline", capture_input=False)
async def compare_repositories(
    request: RepositoriesRequest,
    github_client: GithubClient,
    context: AuthContext = Depends(get_auth_context),
):
    user_id = context.user_id
    db = context.client

    assert user_id is not None

    repositories = request.repositories
    logger.info("Comparing %d repositories for user %s", len(repositories), user_id)

    assert len(repositories) > 1, HTTPException(401, "More than 1 repos are required")

    record_input(repositories=[repo.full_name for repo in repositories])
    with propagate_attributes(
        user_id=str(user_id), metadata={"mode": "compare", "repo_count": len(repositories)}
    ):
        readme = await _fetch_readmes(github_client, repositories, "compare")
        report = await generate_report(list(zip(repositories, readme, strict=True)), "compare")

    response = ComparisonResponse(
        comparison_id=str(uuid.uuid4()),
        comparison=render_report_markdown(report),
        selected_repos=repositories,
        missing_readme=_missing_readme(repositories, readme),
        report=report,
        report_type="compare",
    )
    # Columns mirror ComparisonResponse; the LLM report is stored whole in the `report` jsonb column.
    db.table("comparisons").insert(
        {**response.model_dump(mode="json"), "user_id": str(user_id)}
    ).execute()
    logger.info("Saved comparison %s", response.comparison_id)
    return response
