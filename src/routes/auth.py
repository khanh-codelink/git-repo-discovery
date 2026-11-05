from fastapi import APIRouter, Depends

from src.auth.dependencies import AuthContext, get_auth_context
from src.shared.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


# Protected Endpoints
@router.get("/api/profile")
def get_user_profile(context: AuthContext = Depends(get_auth_context)):
    db = context.client
    response = db.table("profiles").select("*").execute()
    if not response.data:
        logger.info("No profile found for user %s", context.user_id)
        return {"data": None, "message": "User profile not found"}
    return {"data": response.data}
