import uuid

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from github import Github

from src.agents.search_query import UNSUPPORTED, analyze_query
from src.auth.github_check import GithubClient
from src.models.response_model import RepoResult, SearchQuery, SearchResponse

router = APIRouter()


def _search_github(github_client: Github, query: str, limit: int) -> list[RepoResult]:
    """Run the GitHub search (blocking: PyGithub fetches pages lazily while iterating)."""
    repositories = github_client.search_repositories(query=query)
    return [
        RepoResult(
            repo_id=str(repo.id),
            name=repo.name,
            full_name=repo.full_name,
            topics=repo.topics,
            description=repo.description,
            html_url=repo.html_url,
            stargazers_count=repo.stargazers_count,
        )
        for repo in repositories[:limit]
    ]


@router.post("/search", response_model=SearchResponse)
async def search_repositories(search_query: SearchQuery, github_client: GithubClient):
    analyzed_query = await analyze_query(search_query.query)
    if analyzed_query == UNSUPPORTED:
        raise HTTPException(status_code=400, detail="Query not supported")

    repo_results = await run_in_threadpool(
        _search_github, github_client, analyzed_query, search_query.limit
    )
    return SearchResponse(
        search_id=str(uuid.uuid4()),
        search_query=search_query.query,
        analyzed_query=analyzed_query,
        text_response=analyzed_query,
        search_results=repo_results,
    )
