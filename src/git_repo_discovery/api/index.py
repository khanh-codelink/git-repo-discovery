import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.git_repo_discovery.api.router import router

load_dotenv()

app = FastAPI()

# CORS Configuration
# Allows your React frontend (local dev + Vercel deployment) to talk to this API
allowed_origins = [
    "http://localhost:3000",  # React local development
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
