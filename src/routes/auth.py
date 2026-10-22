from dataclasses import dataclass

from fastapi import APIRouter, Depends, Header, HTTPException
from supabase import Client, create_client

from src.config import get_settings


@dataclass(frozen=True)
class AuthContext:
    client: Client
    user_id: str


config = get_settings()
router = APIRouter()

# Initialize Supabase Client (Use the public ANON key, NOT the service_role key)
SUPABASE_URL = config.supabase_url
SUPABASE_ANON_KEY = config.supabase_key.get_secret_value()

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY environment variables")


# Authentication & RLS Dependency
def get_auth_context(authorization: str = Header(None)) -> AuthContext:
    """
    Extracts the Bearer token sent by React, verifies the Google OAuth user session,
    and configures the Supabase client so Postgres RLS policies (auth.uid()) apply.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = authorization.split(" ")[1]

    try:
        client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        # Verify that the JWT is valid with Supabase
        user_response = client.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        # Set the token session so all database queries executed by this client respect RLS
        client.auth.set_session(access_token=token, refresh_token=token)
        return AuthContext(client=client, user_id=user_response.user.id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")


def get_authenticated_client(auth_context: AuthContext = Depends(get_auth_context)) -> Client:
    return auth_context.client


# Protected Endpoints
@router.get("/api/profile")
def get_user_profile(db: Client = Depends(get_authenticated_client)):
    # Querying the 'profiles' table will automatically apply RLS for the logged-in Google user
    response = db.table("profiles").select("*").execute()
    if not response.data:
        return {"data": None, "message": "User profile not found"}
    return {"data": response.data}
