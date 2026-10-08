from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureOpenAIConfig(BaseSettings):
    """Configuration for Azure OpenAI API, read from `AZURE_OPENAI_*` env vars."""

    model_config = SettingsConfigDict(
        env_prefix="AZURE_OPENAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    provider: Literal["azure_openai"] = "azure_openai"

    api_key: SecretStr
    endpoint: str
    model_name: str
    endpoint_version: str = "2023-06-01-preview"
    deployment_name: str


class GitRepoDiscoveryConfig(BaseSettings):
    """Configuration for Git repository discovery."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    github_token: SecretStr
    llm_settings: AzureOpenAIConfig = Field(default_factory=AzureOpenAIConfig)


@lru_cache
def get_config() -> GitRepoDiscoveryConfig:
    """Get the configuration for Git repository discovery."""
    return GitRepoDiscoveryConfig()


def get_settings() -> GitRepoDiscoveryConfig:
    """Get the settings for Git repository discovery."""
    return get_config()
