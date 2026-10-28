from fastapi import APIRouter, Depends

from src.auth.dependencies import AuthContext, get_auth_context
from src.config import get_settings

config = get_settings()
router = APIRouter()


# Protected Endpoints
@router.get("/api/profile")
def get_user_profile(context: AuthContext = Depends(get_auth_context)):
    db = context.client
    response = db.table("profiles").select("*").execute()
    if not response.data:
        return {"data": None, "message": "User profile not found"}
    return {"data": response.data}
