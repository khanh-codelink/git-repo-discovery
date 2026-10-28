from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.auth.dependencies import AuthContext, get_auth_context
from src.routes.git_repo import router


@pytest.fixture
def api():
    db = MagicMock()
    app = FastAPI()
    app.include_router(router)

    def authenticated_user():
        return AuthContext(client=db, user_id="user-1")

    app.dependency_overrides[get_auth_context] = authenticated_user
    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        app.dependency_overrides.clear()


def test_list_empty_repositories(api):
    client, db = api

    table = db.table.return_value
    selection = table.select.return_value
    owner_filter = selection.eq.return_value
    paginated = owner_filter.range.return_value
    paginated.execute.return_value = MagicMock(data=[], count=0)

    payload = {"page": 1, "per_page": 10}
    response = client.post("/repositories", json=payload)

    assert response.status_code == 200
    db.table.assert_called_once_with("repositories")
    table.select.assert_called_once_with("*", count="exact")
    selection.eq.assert_called_once_with("user_id", "user-1")
    owner_filter.range.assert_called_once_with(0, 9)
    paginated.execute.assert_called_once_with()
    assert response.json() == {"items": [], "total": 0, "page": 1, "per_page": 10}


def test_list_repositories(api):
    client, db = api
    mock_data = [
        {
            "id": 1,
            "repo_id": "repo-1",
            "name": "Repo 1",
            "full_name": "user/Repo 1",
            "description": "Description 1",
            "html_url": "http://example.com/repo-1",
            "stargazers_count": 10,
            "user_id": "user-1",
        }
    ]

    table = db.table.return_value
    selection = table.select.return_value
    owner_filter = selection.eq.return_value
    paginated = owner_filter.range.return_value
    paginated.execute.return_value = MagicMock(data=mock_data, count=27)

    response = client.post("/repositories", json={"page": 1, "per_page": 10})

    assert response.status_code == 200
    db.table.assert_called_once_with("repositories")
    table.select.assert_called_once_with("*", count="exact")
    selection.eq.assert_called_once_with("user_id", "user-1")
    owner_filter.range.assert_called_once_with(0, 9)
    paginated.execute.assert_called_once_with()
    assert response.json() == {"items": mock_data, "total": 27, "page": 1, "per_page": 10}


def test_save_repository(api):
    client, db = api
    payload = {
        "repositories": [
            {
                "repo_id": "repo-1",
                "name": "Repo 1",
                "full_name": "user/Repo 1",
                "description": "Description 1",
                "html_url": "http://example.com/repo-1",
                "stargazers_count": 10,
            }
        ]
    }
    table = db.table.return_value

    response = client.post("/save-repositories", json=payload)

    assert response.status_code == 200
    db.table.assert_called_once_with("repositories")
    table.insert.assert_called_once_with([{**payload["repositories"][0], "user_id": "user-1"}])


def test_save_multiple_repositories(api):
    client, db = api
    payload = {
        "repositories": [
            {
                "repo_id": "repo-1",
                "name": "Repo 1",
                "full_name": "user/Repo 1",
                "description": "Description 1",
                "html_url": "http://example.com/repo-1",
                "stargazers_count": 10,
            },
            {
                "repo_id": "repo-2",
                "name": "Repo 2",
                "full_name": "user/Repo 2",
                "description": "Description 2",
                "html_url": "http://example.com/repo-2",
                "stargazers_count": 20,
            },
        ]
    }
    table = db.table.return_value

    response = client.post("/save-repositories", json=payload)

    assert response.status_code == 200
    db.table.assert_called_once_with("repositories")
    table.insert.assert_called_once_with(
        [
            {**payload["repositories"][0], "user_id": "user-1"},
            {**payload["repositories"][1], "user_id": "user-1"},
        ]
    )


def test_save_no_repositories(api):
    client, db = api
    payload = {"repositories": []}
    table = db.table.return_value

    response = client.post("/save-repositories", json=payload)

    assert response.status_code == 200
    db.table.assert_called_once_with("repositories")
    table.insert.assert_called_once_with([])


def test_delete_repository(api):
    client, db = api
    table = db.table.return_value
    deletion = table.delete.return_value
    owner_filter = deletion.eq.return_value

    response = client.delete("/repositories/repo-1")

    assert response.status_code == 200
    db.table.assert_called_once_with("repositories")
    table.delete.assert_called_once()
    deletion.eq.assert_called_once_with("user_id", "user-1")
    owner_filter.eq.assert_called_once_with("id", "repo-1")
