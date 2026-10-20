from fastapi import APIRouter, Depends, HTTPException
from postgrest.types import ReturnMethod
from supabase import Client

from src.routes.auth import get_authenticated_client
from src.schemas.repository_shema import (
    RepositoryResponse,
    SaveRepositoryInput,
    SaveRepositoryResponse,
)

router = APIRouter()


@router.post("/save-repositories", response_model=SaveRepositoryResponse)
async def save_repositories(
    input: SaveRepositoryInput, db: Client = Depends(get_authenticated_client)
):
    user = db.auth.get_user().user
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    rows = [
        {**repo.model_dump(mode="json"), "user_id": str(user.id)} for repo in input.repositories
    ]
    db.table("repositories").insert(rows, returning=ReturnMethod.minimal).execute()
    return SaveRepositoryResponse(success=True)


@router.get("/repositories", response_model=list[RepositoryResponse])
async def get_repositories(db: Client = Depends(get_authenticated_client)):
    user = db.auth.get_user().user
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    response = db.table("repositories").select("*").eq("user_id", str(user.id)).execute()
    return response.data


@router.delete("/repositories/{repo_id}", response_model=SaveRepositoryResponse)
async def delete_repository(repo_id: str, db: Client = Depends(get_authenticated_client)):
    user = db.auth.get_user().user
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    db.table("repositories").delete().eq("user_id", str(user.id)).eq("repo_id", repo_id).execute()
    return SaveRepositoryResponse(success=True)
