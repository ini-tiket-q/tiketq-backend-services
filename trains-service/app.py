from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")
print("TRAINS_DB_URL:", os.getenv("TRAINS_DB_URL"))

from routes.trains_route import router as trains_router

app = FastAPI(
    title="TiketQ Trains Service",
    description="Train booking and schedule service for TiketQ platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Stations",
            "description": "Endpoints for train stations data and search"
        },
        {
            "name": "Train Search",
            "description": "Search and view train schedules"
        }
    ]
)

app.include_router(trains_router, tags=["Stations", "Train Search"])

from adapters.db import Base, engine

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "trains-service",
        "environment": os.getenv("ENV", "development"),
        "db_url_present": bool(os.getenv("TRAINS_DB_URL")),
        "api_key_present": bool(os.getenv("KAI_API_KEY"))
    }