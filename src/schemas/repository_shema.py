from pydantic import BaseModel, Field


class RepoInput(BaseModel):
    repo_id: str = Field(..., description="The unique identifier of the repository.")
    name: str = Field(..., description="The name of the repository.")
    full_name: str = Field(..., description="The full name of the repository, including the owner.")
    description: str | None = Field(None, description="A brief description of the repository.")
    html_url: str = Field(..., description="The URL to access the repository on GitHub.")
    stargazers_count: int = Field(
        ..., description="The number of stars the repository has received."
    )


class GetRepositoriesInput(BaseModel):
    page: int | None = Field(None, description="The page number for pagination.")
    per_page: int | None = Field(None, description="The number of items per page.")
    filter: dict | None = Field(None, description="Filter criteria for repositories.")
    sort_by: str | None = Field(None, description="Sort order for the repositories.")


class SaveRepositoryInput(BaseModel):
    repositories: list[RepoInput] = Field(..., description="A list of repositories to be saved.")


class SaveRepositoryResponse(BaseModel):
    success: bool = Field(
        ..., description="Indicates whether the repositories were successfully saved."
    )


class RepositoryResponse(BaseModel):
    id: int = Field(
        ..., description="The unique identifier of the repository record in the database."
    )
    repo_id: str = Field(..., description="The unique identifier of the repository.")
    name: str = Field(..., description="The name of the repository.")
    full_name: str = Field(..., description="The full name of the repository, including the owner.")
    description: str | None = Field(None, description="A brief description of the repository.")
    html_url: str = Field(..., description="The URL to access the repository on GitHub.")
    stargazers_count: int = Field(
        ..., description="The number of stars the repository has received."
    )
    user_id: str = Field(..., description="The ID of the user who saved the repository.")


class GetRepositoriesResponse(BaseModel):
    items: list[RepositoryResponse] = Field(
        ..., description="A list of repositories matching the query."
    )
    total: int = Field(..., description="The total number of repositories matching the query.")
    page: int | None = Field(None, description="The current page number for pagination.")
    per_page: int | None = Field(None, description="The number of items per page for pagination.")
