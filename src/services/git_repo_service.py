from src.repositories import git_repo_repository as repo
from src.shared.logging import get_logger

logger = get_logger(__name__)


def save_git_repo(db, user_id, repositories):
    rows = [{**repo.model_dump(mode="json"), "user_id": str(user_id)} for repo in repositories]
    logger.info("Saving %d repositories for user %s", len(rows), user_id)
    return repo.insert_git_repo(db, rows)


def list_git_repos(db, user_id, *, page=None, per_page=None, filter=None, sort_by=None):
    logger.info("Listing repositories for user %s (page %s, per_page %s)", user_id, page, per_page)
    return repo.list_git_repos(
        db, user_id, page=page, per_page=per_page, filter=filter, sort_by=sort_by
    )


def delete_git_repo(db, user_id, repo_id):
    logger.info("Deleting repository %s for user %s", repo_id, user_id)
    return repo.delete_git_repo(db, user_id, repo_id)
