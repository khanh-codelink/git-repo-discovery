from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.auth.dependencies import AuthContext, get_auth_context
from src.routes.auth import router


@pytest.fixture
def api():
    db = MagicMock()
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_auth_context] = lambda: AuthContext(
        client=db,
        user_id="user-1",
    )
    try:
        with TestClient(app) as client:
            yield client, db
    finally:
        app.dependency_overrides.clear()


def test_get_profile_success(api):
    client, db = api
    db.table.return_value.select.return_value.execute.return_value = MagicMock(
        data=[{"id": "user-1", "name": "Test User"}]
    )
    response = client.get("/api/profile")
    assert response.status_code == 200
    assert response.json().get("data")[0] == {"id": "user-1", "name": "Test User"}


def test_get_profile_not_found(api):
    client, db = api
    db.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
    response = client.get("/api/profile")
    assert response.status_code == 200
    assert response.json() == {"data": None, "message": "User profile not found"}


def test_get_profile_error_unauthorized():
    app = FastAPI()
    app.include_router(router)
    with TestClient(app) as client:
        response = client.get("/api/profile")

        assert response.status_code == 401
        assert response.json() == {"detail": "Missing or malformed Authorization header"}
