from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

import src.auth.dependencies as auth_dependencies


@pytest.fixture
def supabase_client(monkeypatch):
    client = MagicMock()
    client.auth.get_user.return_value = SimpleNamespace(user=SimpleNamespace(id="user-1"))

    create_client = MagicMock(return_value=client)
    monkeypatch.setattr(auth_dependencies, "create_client", create_client)
    monkeypatch.setattr(
        auth_dependencies,
        "get_settings",
        lambda: SimpleNamespace(
            supabase_url="https://example.test",
            supabase_key=SimpleNamespace(get_secret_value=lambda: "test-key"),
        ),
    )
    return client, create_client


def test_get_auth_context_accepts_valid_token(supabase_client):
    client, create_client = supabase_client

    context = auth_dependencies.get_auth_context("Bearer test-token")

    assert context.client is client
    assert context.user_id == "user-1"
    create_client.assert_called_once_with("https://example.test", "test-key")
    client.auth.get_user.assert_called_once_with("test-token")
    client.postgrest.auth.assert_called_once_with("test-token")


def test_get_auth_context_rejects_invalid_token(supabase_client):
    client, create_client = supabase_client

    client.auth.get_user.return_value = SimpleNamespace(user=None)

    with pytest.raises(HTTPException) as exc_info:
        auth_dependencies.get_auth_context("Bearer invalid-token")

    assert exc_info.value.status_code == 401


def test_get_auth_context_rejects_missing_authorization_header(supabase_client):
    with pytest.raises(HTTPException) as exc_info:
        auth_dependencies.get_auth_context(None)

    assert exc_info.value.status_code == 401


def test_get_auth_context_rejects_malformed_authorization_header(supabase_client):
    with pytest.raises(HTTPException) as exc_info:
        auth_dependencies.get_auth_context("InvalidHeader")

    assert exc_info.value.status_code == 401
