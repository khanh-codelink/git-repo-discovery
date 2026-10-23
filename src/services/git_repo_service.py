from src.repositories import git_repo_repository as repo


def save_git_repo(db, user_id, repositories):
    rows = [{**repo.model_dump(mode="json"), "user_id": str(user_id)} for repo in repositories]
    return repo.insert_git_repo(db, rows)


def list_git_repos(db, user_id):
    return repo.list_git_repos(db, user_id)


def delete_git_repo(db, user_id, repo_id):
    return repo.delete_git_repo(db, user_id, repo_id)
