import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Export .env into os.environ before the routes are imported: code that reads os.environ
# directly (e.g. FE_APP_DOMAIN below) needs it, while pydantic-settings only loads .env into
# its config objects. Variables that are already set (e.g. on the host) win.
load_dotenv()

from src.services.observability import flush_langfuse, init_langfuse  # noqa: E402

from .router import router  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_langfuse()
    yield
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

app.include_router(router)


@app.get("/")
def health_check():
    return {"status": "online", "message": "Python backend running on Vercel"}
