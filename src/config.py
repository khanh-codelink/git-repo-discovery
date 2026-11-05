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


class LangfuseConfig(BaseSettings):
    """Configuration for Langfuse tracing, read from `LANGFUSE_*` env vars.

    Every field is optional: without keys the app runs normally with tracing off.
    """

    model_config = SettingsConfigDict(
        env_prefix="LANGFUSE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    public_key: str | None = None
    secret_key: SecretStr | None = None
    # The SDK deprecated LANGFUSE_HOST in favour of LANGFUSE_BASE_URL.
    base_url: str = "http://localhost:3000"
    tracing_enabled: bool = True

    @property
    def is_active(self) -> bool:
        return self.tracing_enabled and bool(self.public_key and self.secret_key)


class GitRepoDiscoveryConfig(BaseSettings):
    """Configuration for Git repository discovery."""

    loglevel: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    github_token: SecretStr

    supabase_url: str
    supabase_key: SecretStr

    llm_settings: AzureOpenAIConfig = Field(default_factory=AzureOpenAIConfig)


@lru_cache
def get_config() -> GitRepoDiscoveryConfig:
    """Get the configuration for Git repository discovery."""
    return GitRepoDiscoveryConfig()


def get_settings() -> GitRepoDiscoveryConfig:
    """Get the settings for Git repository discovery."""
    return get_config()


@lru_cache
def get_langfuse_config() -> LangfuseConfig:
    """Get the Langfuse settings.

    Kept separate from GitRepoDiscoveryConfig so a missing app setting can never stop
    tracing from initialising, and missing Langfuse keys can never stop the app.
    """
    return LangfuseConfig()
