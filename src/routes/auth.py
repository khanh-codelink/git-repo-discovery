from fastapi import APIRouter, Depends
from supabase import Client
from src.config import get_settings
from src.auth.dependencies import get_authenticated_client

config = get_settings()
router = APIRouter()

# Protected Endpoints
@router.get("/api/profile")
def get_user_profile(db: Client = Depends(get_authenticated_client)):
    # Querying the 'profiles' table will automatically apply RLS for the logged-in Google user
    response = db.table("profiles").select("*").execute()
    if not response.data:
        return {"data": None, "message": "User profile not found"}
    return {"data": response.data}
