from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from supabase import Client, create_client

from src.config import get_settings


@dataclass(frozen=True)
class AuthContext:
    client: Client
    user_id: str


# Authentication & RLS Dependency
def get_auth_context(authorization: str | None = Header(None)) -> AuthContext:
    """
    Extracts the Bearer token sent by React, verifies the Google OAuth user session,
    and configures the Supabase client so Postgres RLS policies (auth.uid()) apply.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    config = get_settings()
    client = create_client(
        config.supabase_url,
        config.supabase_key.get_secret_value(),
    )
    token = authorization.split(" ")[1]

    try:
        # Verify that the JWT is valid with Supabase
        user_response = client.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        client.postgrest.auth(token)
        return AuthContext(client=client, user_id=user_response.user.id)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")


def get_authenticated_client(auth_context: AuthContext = Depends(get_auth_context)) -> Client:
    return auth_context.client
