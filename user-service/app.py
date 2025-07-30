from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

from routes.user_routes import router

app = FastAPI(
    title="TiketQ User Service",
    description="User profile management service with Role-Based Access Control (RBAC)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "User Profiles",
            "description": "User profile management operations with RBAC protection"
        },
        {
            "name": "User Management",
            "description": "Admin-only user management operations"
        }
    ]
)

app.include_router(router, prefix="/users", tags=["User Profiles", "User Management"])

from adapters.db import Base, engine

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine) 