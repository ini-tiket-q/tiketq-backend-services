from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path
import os

# Load all env vars from root .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from routes.auth_routes import router

app = FastAPI()
app.include_router(router, prefix="/auth")

# Optional: create tables automatically at startup (for dev)
from adapters.db import Base, engine

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
