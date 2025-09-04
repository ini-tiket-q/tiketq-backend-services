from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
from routes.auth_routes import router

# Load all env vars from root .env
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

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

# Add CORS middleware to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js frontend
        "http://127.0.0.1:3000",  # Alternative localhost
        "https://localhost:3000",  # HTTPS version
        "https://127.0.0.1:3000",  # HTTPS alternative
    ],
    allow_credentials=True,  # Allow cookies/auth headers
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

app.include_router(router, prefix="/auth", tags=["Authentication", "User Management"])

# Optional: create tables automatically at startup (for dev)
from adapters.db import Base, engine

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
