from fastapi import APIRouter, Depends

from src.auth.dependencies import AuthContext, get_auth_context
from src.schemas.repository_shema import (
    GetRepositoriesInput,
    GetRepositoriesResponse,
    SaveRepositoryInput,
    SaveRepositoryResponse,
)
from src.services import git_repo_service as service
from src.shared.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/save-repositories", response_model=SaveRepositoryResponse)
async def save_repositories(
    input: SaveRepositoryInput, context: AuthContext = Depends(get_auth_context)
):
    service.save_git_repo(context.client, context.user_id, input.repositories)
    return SaveRepositoryResponse(success=True)


@router.post("/repositories", response_model=GetRepositoriesResponse)
async def get_repositories(
    input: GetRepositoriesInput, context: AuthContext = Depends(get_auth_context)
):
    response = service.list_git_repos(
        context.client,
        context.user_id,
        page=input.page,
        per_page=input.per_page,
        filter=input.filter,
        sort_by=input.sort_by,
    )
    logger.info("Returning %d of %s saved repositories", len(response.data), response.count)
    return GetRepositoriesResponse(
        items=response.data, total=response.count, page=input.page, per_page=input.per_page
    )


@router.delete("/repositories/{repo_id}", response_model=SaveRepositoryResponse)
async def delete_repository(repo_id: str, context: AuthContext = Depends(get_auth_context)):
    service.delete_git_repo(context.client, context.user_id, repo_id)
    return SaveRepositoryResponse(success=True)
