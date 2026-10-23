from fastapi import APIRouter, Depends

from src.auth.dependencies import AuthContext, get_auth_context
from src.schemas.repository_shema import (
    RepositoryResponse,
    SaveRepositoryInput,
    SaveRepositoryResponse,
)
from src.services import git_repo_service as service

router = APIRouter()


@router.post("/save-repositories", response_model=SaveRepositoryResponse)
async def save_repositories(
    input: SaveRepositoryInput, context: AuthContext = Depends(get_auth_context)
):
    service.save_git_repo(context.client, context.user_id, input.repositories)
    return SaveRepositoryResponse(success=True)


@router.get("/repositories", response_model=list[RepositoryResponse])
async def get_repositories(context: AuthContext = Depends(get_auth_context)):
    response = service.list_git_repos(context.client, context.user_id)
    return response.data


@router.delete("/repositories/{repo_id}", response_model=SaveRepositoryResponse)
async def delete_repository(repo_id: str, context: AuthContext = Depends(get_auth_context)):
    service.delete_git_repo(context.client, context.user_id, repo_id)
    return SaveRepositoryResponse(success=True)
