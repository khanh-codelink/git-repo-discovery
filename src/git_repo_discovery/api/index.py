import os
from fastapi import FastAPI, Depends, HTTPException, Header
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

app = FastAPI()

# Dependency to verify Supabase Auth tokens
def verify_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    
    token = authorization.split(" ")[1]
    try:
        # Verify the JWT with Supabase
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/")
def home():
    return {"message": "Python backend running on Vercel with uv!"}

@app.get("/protected-data")
def get_protected_data(user = Depends(verify_auth)):
    # Example database query using the verified user
    # data = supabase.table("profiles").select("*").eq("id", user.user.id).execute()
    return {"message": "You are authenticated!", "user_id": user.user.id}