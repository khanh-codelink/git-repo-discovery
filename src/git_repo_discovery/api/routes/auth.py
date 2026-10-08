import os

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Header, HTTPException
from supabase import Client, create_client

load_dotenv()
router = APIRouter()

# Initialize Supabase Client (Use the public ANON key, NOT the service_role key)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


# Authentication & RLS Dependency
def get_authenticated_client(authorization: str = Header(None)) -> Client:
    """
    Extracts the Bearer token sent by React, verifies the Google OAuth user session,
    and configures the Supabase client so Postgres RLS policies (auth.uid()) apply.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = authorization.split(" ")[1]

    try:
        # Verify that the JWT is valid with Supabase
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Set the token session so all database queries executed by this client respect RLS
        supabase.auth.set_session(access_token=token, refresh_token=token)
        return supabase
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")


# Protected Endpoints
@router.get("/api/profile")
def get_user_profile(db: Client = Depends(get_authenticated_client)):
    # Querying the 'profiles' table will automatically apply RLS for the logged-in Google user
    response = db.table("profiles").select("*").execute()
    if not response.data:
        return {"data": None, "message": "User profile not found"}
    return {"data": response.data}
