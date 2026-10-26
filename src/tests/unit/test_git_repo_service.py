from unittest.mock import Mock

from src.schemas.repository_shema import RepoInput
from src.services import git_repo_service as service


def test_save_git_repo_calls_insert(monkeypatch):
    db = Mock()
    repository = RepoInput(
        repo_id="123",
        name="demo",
        full_name="owner/demo",
        html_url="https://github.com/owner/demo",
        stargazers_count=10,
    )
    insert = Mock()
    monkeypatch.setattr(service.repo, "insert_git_repo", insert)

    service.save_git_repo(db, "user-1", [repository])

    insert.assert_called_once_with(
        db, [{**repository.model_dump(mode="json"), "user_id": "user-1"}]
    )


def test_save_git_repo_calls_insert_with_multiple_repositories(monkeypatch):
    db = Mock()
    repositories = [
        RepoInput(
            repo_id="123",
            name="demo",
            full_name="owner/demo",
            html_url="https://github.com/owner/demo",
            stargazers_count=10,
        ),
        RepoInput(
            repo_id="456",
            name="demo2",
            full_name="owner/demo2",
            html_url="https://github.com/owner/demo2",
            stargazers_count=20,
        ),
    ]
    insert = Mock()
    monkeypatch.setattr(service.repo, "insert_git_repo", insert)

    service.save_git_repo(db, "user-1", repositories)

    insert.assert_called_once_with(
        db,
        [
            {**repositories[0].model_dump(mode="json"), "user_id": "user-1"},
            {**repositories[1].model_dump(mode="json"), "user_id": "user-1"},
        ],
    )


def test_save_git_repo_calls_insert_with_empty_list(monkeypatch):
    db = Mock()
    insert = Mock()
    monkeypatch.setattr(service.repo, "insert_git_repo", insert)

    service.save_git_repo(db, "user-1", [])

    insert.assert_called_once_with(db, [])


def test_select_git_repo_calls_select(monkeypatch):
    db = Mock()
    select = Mock()
    monkeypatch.setattr(service.repo, "list_git_repos", select)

    service.list_git_repos(db, "user-1")

    select.assert_called_once_with(db, "user-1")


def test_delete_git_repo_calls_delete(monkeypatch):
    db = Mock()
    delete = Mock()
    monkeypatch.setattr(service.repo, "delete_git_repo", delete)

    service.delete_git_repo(db, "user-1", "123")

    delete.assert_called_once_with(db, "user-1", "123")
