from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

from routes.flights import router as flights_router

from adapters.repository_sqlachemy import init_db  
from routes.bookings import router as bookings_router

PORT = int(os.getenv("PORT", 5001))
DB_URL = os.getenv("FLIGHTS_DB_URL")
FLIGHT_API_KEY = os.getenv("EXTERNAL_FLIGHT_API_KEY")

app = FastAPI(
    title="TiketQ Flights Service",
    version="0.2.0",
    description="CRUD + external search (MMBC) — hexagonal architecture."
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
app.include_router(bookings_router)
