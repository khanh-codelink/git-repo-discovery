from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from langfuse.langchain import CallbackHandler

from src.auth.github_check import authorize_github_token
from src.config import LangfuseConfig
from src.services import observability


def _use_langfuse_config(monkeypatch: pytest.MonkeyPatch, **fields) -> None:
    # Explicit values win over env vars and .env, so the developer's own keys can't leak in.
    config = LangfuseConfig(**{"public_key": None, "secret_key": None, **fields})
    monkeypatch.setattr(observability, "get_langfuse_config", lambda: config)


def test_llm_run_config_without_keys_has_no_callbacks(monkeypatch):
    _use_langfuse_config(monkeypatch)

    config = observability.llm_run_config("summarization", tags=["summary"], metadata={"k": "v"})

    assert config == {"run_name": "summarization", "tags": ["summary"], "metadata": {"k": "v"}}


def test_llm_run_config_with_keys_attaches_langfuse_handler(monkeypatch):
    _use_langfuse_config(monkeypatch, public_key="pk-lf-test", secret_key="sk-lf-test")

    config = observability.llm_run_config("keyword extraction")

    assert config["run_name"] == "keyword extraction"
    assert len(config["callbacks"]) == 1
    assert isinstance(config["callbacks"][0], CallbackHandler)


def test_llm_run_config_respects_tracing_disabled(monkeypatch):
    _use_langfuse_config(
        monkeypatch, public_key="pk-lf-test", secret_key="sk-lf-test", tracing_enabled=False
    )

    assert "callbacks" not in observability.llm_run_config("comparison")


def test_search_works_with_tracing_disabled(monkeypatch):
    _use_langfuse_config(monkeypatch, tracing_enabled=False)

    from src.main import app
    from src.routes import search

    async def fake_analyze_query(text: str) -> str:
        return "fastapi language:python"

    repo = MagicMock(
        id=1,
        full_name="tiangolo/fastapi",
        topics=["python"],
        description="FastAPI framework",
        html_url="https://github.com/tiangolo/fastapi",
        stargazers_count=1,
    )
    repo.name = "fastapi"  # `name` is a MagicMock constructor argument, so set it separately
    github_client = MagicMock()
    github_client.search_repositories.return_value = [repo]

    monkeypatch.setattr(search, "analyze_query", fake_analyze_query)
    app.dependency_overrides[authorize_github_token] = lambda: github_client
    try:
        with TestClient(app) as client:  # runs the lifespan, so init_langfuse() runs too
            response = client.post("/search", json={"query": "python web frameworks"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert [r["full_name"] for r in response.json()["search_results"]] == ["tiangolo/fastapi"]
