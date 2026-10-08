from functools import lru_cache
from typing import Annotated, Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureOpenAIConfig(BaseModel):
    """Configuration for Azure OpenAI API."""

    provider: Literal["azure_openai"] = "azure_openai"

    api_key: str
    endpoint: str
    model_name: str
    endpoint_version: Literal["2023-03-15-preview", "2023-06-01-preview"] = "2023-06-01-preview"
    deployment_name: str


LLMSettings = Annotated[AzureOpenAIConfig, Field(discriminator="provider")]


class GitRepoDiscoveryConfig(BaseSettings):
    """Configuration for Git repository discovery."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    github_token: Annotated[str, Field(env="GITHUB_TOKEN")]
    llm_settings: LLMSettings = AzureOpenAIConfig()


@lru_cache
def get_config() -> GitRepoDiscoveryConfig:
    """Get the configuration for Git repository discovery."""
    return GitRepoDiscoveryConfig()


def get_settings() -> GitRepoDiscoveryConfig:
    """Get the settings for Git repository discovery."""
    return get_config()


settings = get_settings()
