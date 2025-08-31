from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path
import os

# Load all env vars from root .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from routes.auth_routes import router

app = FastAPI(
    title="TiketQ Auth Service",
    description="Authentication and Authorization service with Role-Based Access Control (RBAC)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "User authentication and authorization endpoints"
        },
        {
            "name": "User Management",
            "description": "Admin-only user management operations"
        }
    ]
)

app.include_router(router, prefix="/auth", tags=["Authentication", "User Management"])

# Optional: create tables automatically at startup (for dev)
from adapters.db import Base, engine

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
