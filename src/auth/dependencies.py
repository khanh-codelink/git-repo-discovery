from dataclasses import dataclass

from fastapi import Header, HTTPException
from supabase import Client, create_client

from src.config import get_settings
from src.shared.logging import get_logger

logger = get_logger(__name__)


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
        logger.warning("Rejected request: missing or malformed Authorization header")
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
            logger.warning("Rejected request: Supabase returned no user for the token")
            raise HTTPException(status_code=401, detail="Invalid or expired token")

        client.postgrest.auth(token)
        logger.debug("Authenticated Supabase user %s", user_response.user.id)
        return AuthContext(client=client, user_id=user_response.user.id)
    except Exception as e:
        # Log the error type only: the message can echo the token back.
        logger.warning("Supabase token verification failed: %s", type(e).__name__)
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")
