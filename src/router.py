from fastapi import APIRouter

from .routes import auth, git_repo, search

router = APIRouter()

router.include_router(auth.router)
router.include_router(search.router)
router.include_router(git_repo.router)
