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


class SaveRepositoryInput(BaseModel):
    repositories: list[RepoInput] = Field(..., description="A list of repositories to be saved.")


class SaveRepositoryResponse(BaseModel):
    success: bool = Field(
        ..., description="Indicates whether the repositories were successfully saved."
    )


class RepositoryResponse(RepoInput):
    id: int = Field(
        ..., description="The unique identifier of the repository record in the database."
    )
    user_id: str = Field(..., description="The ID of the user who saved the repository.")
