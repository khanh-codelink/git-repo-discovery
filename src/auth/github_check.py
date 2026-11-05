from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from github import Auth, BadCredentialsException, Github, GithubException

from src.config import get_settings
from src.shared.logging import get_logger

config = get_settings()
logger = get_logger(__name__)

bearer_scheme = HTTPBearer()


def authorize_github_token() -> Github:
    """Verify the GitHub token from the Authorization header and return a client."""
    github_client = Github(auth=Auth.Token(config.github_token.get_secret_value()))
    try:
        _ = github_client.get_user().login  # get_user() is lazy; .login makes the API call
    except BadCredentialsException:
        logger.error("GitHub rejected the configured GITHUB_TOKEN (bad credentials)")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid GitHub token")
    except GithubException as e:
        logger.error("Could not verify GITHUB_TOKEN with GitHub (status %s)", e.status)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail="Could not verify token with GitHub"
        )
    return github_client


GithubClient = Annotated[Github, Depends(authorize_github_token)]
