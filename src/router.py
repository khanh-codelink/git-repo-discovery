from fastapi import APIRouter

from .routes import auth, search, repository

router = APIRouter()

router.include_router(auth.router)
router.include_router(search.router)
router.include_router(repository.router)
