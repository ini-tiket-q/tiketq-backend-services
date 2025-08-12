from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from routes.flights import router as flights_router
from adapters.persistence import init_db  # <-- use the imported one

PORT = int(os.getenv("PORT", 5001))
DB_URL = os.getenv("FLIGHTS_DB_URL")
FLIGHT_API_KEY = os.getenv("EXTERNAL_FLIGHT_API_KEY")

app = FastAPI(
    title="Flights Service",
    description="Flight schedules CRUD with pagination and soft delete.",
    version="1.0.0",
)


@app.on_event("startup")
def _startup():
    init_db()  # <-- call the imported function

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "port": PORT,
        "db_url_present": bool(DB_URL),
        "api_key_present": bool(FLIGHT_API_KEY)
    }

app.include_router(flights_router)
