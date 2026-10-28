from unittest.mock import MagicMock

from src.repositories import git_repo_repository as repository


def test_list_git_repos_by_owner():
    db = MagicMock()
    table = db.table.return_value
    selection = table.select.return_value
    filtered = selection.eq.return_value
    expected = filtered.range.return_value.execute.return_value

    result = repository.list_git_repos(db, "user-1", page=1, per_page=10)

    db.table.assert_called_once_with("repositories")
    table.select.assert_called_once_with("*", count="exact")
    selection.eq.assert_called_once_with("user_id", "user-1")
    filtered.range.assert_called_once_with(0, 9)
    assert result is expected


def test_list_git_repos_filters_by_owner():
    db = MagicMock()
    table = db.table.return_value
    selection = table.select.return_value
    filtered = selection.eq.return_value
    expected = filtered.eq.return_value.range.return_value.execute.return_value

    result = repository.list_git_repos(db, "user-1", page=1, per_page=10, filter={"name": "Repo 1"})

    db.table.assert_called_once_with("repositories")
    table.select.assert_called_once_with("*", count="exact")
    selection.eq.assert_called_once_with("user_id", "user-1")
    filtered.eq.assert_called_once_with("name", "Repo 1")
    filtered.eq.return_value.range.assert_called_once_with(0, 9)
    assert result is expected


def test_list_git_repos_sorts_by_column():
    db = MagicMock()
    table = db.table.return_value
    selection = table.select.return_value
    filtered = selection.eq.return_value
    sorted_query = filtered.order.return_value
    expected = sorted_query.range.return_value.execute.return_value

    result = repository.list_git_repos(db, "user-1", page=1, per_page=10, sort_by="name")

    db.table.assert_called_once_with("repositories")
    table.select.assert_called_once_with("*", count="exact")
    selection.eq.assert_called_once_with("user_id", "user-1")
    filtered.order.assert_called_once_with("name")
    sorted_query.range.assert_called_once_with(0, 9)
    assert result is expected


def test_list_git_repos_filters_and_sorts():
    db = MagicMock()
    table = db.table.return_value
    selection = table.select.return_value
    filtered = selection.eq.return_value
    sorted_query = filtered.eq.return_value.order.return_value
    expected = sorted_query.range.return_value.execute.return_value

    result = repository.list_git_repos(
        db, "user-1", page=1, per_page=10, filter={"name": "Repo 1"}, sort_by="name"
    )

    db.table.assert_called_once_with("repositories")
    table.select.assert_called_once_with("*", count="exact")
    selection.eq.assert_called_once_with("user_id", "user-1")
    filtered.eq.assert_called_once_with("name", "Repo 1")
    filtered.eq.return_value.order.assert_called_once_with("name")
    sorted_query.range.assert_called_once_with(0, 9)
    assert result is expected


def test_insert_git_repo_calls_insert():
    db = MagicMock()
    table = db.table.return_value

    repository.insert_git_repo(db, [{"repo_id": "123", "user_id": "user-1"}])

    db.table.assert_called_once_with("repositories")
    table.insert.assert_called_once_with([{"repo_id": "123", "user_id": "user-1"}])


def test_delete_git_repo_calls_delete():
    db = MagicMock()
    deletion = db.table.return_value.delete.return_value
    owner_filtered = deletion.eq.return_value

    repository.delete_git_repo(db, "user-1", "123")

    db.table.assert_called_once_with("repositories")
    deletion.eq.assert_called_once_with("user_id", "user-1")
    owner_filtered.eq.assert_called_once_with("id", "123")
    owner_filtered.eq.return_value.execute.assert_called_once_with()
