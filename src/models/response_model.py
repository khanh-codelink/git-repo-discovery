from datetime import UTC, datetime

from pydantic import BaseModel, Field


class RepoResult(BaseModel):
    repo_id: str = Field(..., description="The unique identifier of the repository.")
    name: str = Field(..., description="The name of the repository.")
    full_name: str = Field(..., description="The full name of the repository, including the owner.")
    description: str | None = Field(None, description="A brief description of the repository.")
    html_url: str = Field(..., description="The URL to access the repository on GitHub.")
    stargazers_count: int = Field(
        ..., description="The number of stars the repository has received."
    )


class SearchResponse(BaseModel):
    search_id: str = Field(..., description="A unique identifier for the search operation.")
    search_query: str = Field(..., description="The search query used to find repositories.")
    analyzed_query: str = Field(..., description="The analyzed query returned by the LLM.")
    text_response: str = Field(..., description="The response text from the LLM.")
    search_results: list[RepoResult] | None = Field(
        None, description="The list of search results from GitHub."
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SummaryResponse(BaseModel):
    summary_id: str = Field(..., description="A unique identifier for the summary operation.")
    summary: str = Field(..., description="The summary of the repository.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    selected_repo: RepoResult | None = Field(
        None, description="The selected repository for which the summary was generated."
    )


class ComparisonResponse(BaseModel):
    comparison_id: str = Field(..., description="A unique identifier for the comparison operation.")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    selected_repos: list[RepoResult] | None = Field(
        None,
        description="The list of selected repositories for which the comparison was generated.",
    )
    criteria: list[str] | None = Field(
        None, description="The list of criteria used for comparison."
    )


class SearchQuery(BaseModel):
    query: str = Field(..., description="The search query to find repositories.")
    limit: int | None = Field(10, description="The maximum number of repositories to return.")
