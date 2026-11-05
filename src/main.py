import os
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# Export .env into os.environ before the routes are imported: code that reads os.environ
# directly (e.g. FE_APP_DOMAIN below) needs it, while pydantic-settings only loads .env into
# its config objects. Variables that are already set (e.g. on the host) win.
load_dotenv()

from src.shared.logging import get_logger, setup_logging  # noqa: E402

# Before the other imports, so their module loggers propagate to this one root handler.
setup_logging()

from src.services.observability import flush_langfuse, init_langfuse  # noqa: E402

from .router import router  # noqa: E402

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting git-repo-discovery API")
    init_langfuse()
    yield
    logger.info("Shutting down git-repo-discovery API")
    # Langfuse sends traces in background batches; send what's left before shutting down.
    flush_langfuse()


app = FastAPI(lifespan=lifespan)

# CORS Configuration
# Allows your React frontend (local dev + Vercel deployment) to talk to this API
allowed_origins = [
    "http://localhost:3000",  # React local development
    "http://localhost:5173",
    os.environ.get("FE_APP_DOMAIN"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = (time.perf_counter() - start) * 1000
        logger.exception("%s %s failed after %.0f ms", request.method, request.url.path, elapsed_ms)
        raise
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %d (%.0f ms)",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


app.include_router(router)


@app.get("/")
def health_check():
    return {"status": "online", "message": "Python backend running for Git repo discovery"}
