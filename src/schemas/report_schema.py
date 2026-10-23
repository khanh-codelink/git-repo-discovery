from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.schemas.repository_shema import RepoInput

# Keeps the prompt within the model's context window (READMEs are ~6k chars each).
MAX_REPORT_REPOSITORIES = 5

# The LLM fills RepoComparisonReport via structured output (strict JSON schema),
# so its models keep every field required and avoid defaults.


class RepoResult(BaseModel):
    repo_id: str = Field(..., description="The unique identifier of the repository.")
    name: str = Field(..., description="The name of the repository.")
    topics: list[str] = Field(..., description="The list of topics associated with the repository.")
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


class SearchQuery(BaseModel):
    query: str = Field(..., description="The search query to find repositories.")
    limit: int = Field(
        10, ge=1, le=100, description="The maximum number of repositories to return."
    )


class RepoAnalysis(BaseModel):
    full_name: str = Field(..., description="The full name of the repository, including the owner.")
    summary: str = Field(..., description="A 2-3 sentence summary of what the repository does.")
    key_features: list[str] = Field(..., description="The main features of the repository.")
    tech_stack: list[str] = Field(
        ..., description="Languages, frameworks and notable dependencies the repository uses."
    )
    use_cases: list[str] = Field(..., description="Situations the repository is a good fit for.")
    strengths: list[str] = Field(..., description="What the repository does well.")
    limitations: list[str] = Field(
        ..., description="Gaps, caveats or missing information about the repository."
    )


class CriterionAssessment(BaseModel):
    full_name: str = Field(..., description="The full name of the repository being assessed.")
    assessment: str = Field(..., description="How the repository does on this criterion.")


class ComparisonCriterion(BaseModel):
    criterion: str = Field(
        ..., description="The comparison criterion, e.g. 'Ease of setup' or 'Extensibility'."
    )
    assessments: list[CriterionAssessment] = Field(
        ..., description="One assessment per repository for this criterion."
    )
    best_fit: str = Field(
        ..., description="The full name of the repository that does best on this criterion."
    )


class RepoReport(BaseModel):
    overview: str = Field(
        ..., description="A short overview of the selected repositories and how they relate."
    )
    repositories: list[RepoAnalysis] = Field(..., description="One analysis per repository.")
    comparison: list[ComparisonCriterion] = Field(
        ..., description="Criteria comparing the repositories; empty for a single repository."
    )
    recommendation: str = Field(
        ..., description="Which repository to choose for which needs, and why."
    )


class RepositoriesRequest(BaseModel):
    repositories: list[RepoInput] = Field(
        ...,
        min_length=1,
        max_length=MAX_REPORT_REPOSITORIES,
        description="The repositories to summarise; more than one adds a comparison.",
    )


class SummaryResponse(BaseModel):
    summary_id: str = Field(..., description="A unique identifier for the summary operation.")
    summary: str = Field(..., description="The report rendered as markdown, ready to display.")
    selected_repo: RepoInput | None = Field(
        None, description="The summarised repository, when exactly one was requested."
    )
    missing_readme: list[str] = Field(
        default_factory=list,
        description="Full names of repositories whose README could not be fetched; "
        "they were analysed from their metadata only.",
    )
    report: RepoReport = Field(..., description="The structured LLM-generated report.")
    report_type: Literal["summary", "compare"] = Field(..., description="Report type")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ComparisonResponse(BaseModel):
    comparison_id: str = Field(..., description="A unique identifier for the comparison operation.")
    comparison: str = Field(..., description="The report rendered as markdown, ready to display.")
    selected_repos: list[RepoInput] = Field(..., description="All summarised repositories.")
    missing_readme: list[str] = Field(
        default_factory=list,
        description="Full names of repositories whose README could not be fetched; "
        "they were analysed from their metadata only.",
    )
    report: RepoReport = Field(..., description="The structured LLM-generated report.")
    report_type: Literal["summary", "compare"] = Field(..., description="Report type")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
