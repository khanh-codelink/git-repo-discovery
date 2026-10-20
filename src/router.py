from fastapi import APIRouter

from .routes import auth, report, repository, search

router = APIRouter()

router.include_router(auth.router)
router.include_router(search.router)
router.include_router(repository.router)
router.include_router(report.router)
