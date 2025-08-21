from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path
from routes import routes_flights
import os
from fastapi.middleware.cors import CORSMiddleware

from routes.flights import router as flights_router
from routes.bookings import router as bookings_router

# ✅ Force load from root .env
load_dotenv(dotenv_path=Path('.') / ".env")

# ✅ Confirm these are loaded
PORT = int(os.getenv("PORT", 5001))
DB_URL = os.getenv("FLIGHTS_DB_URL")
FLIGHT_API_KEY = os.getenv("EXTERNAL_FLIGHT_API_KEY")

# Initialize FastAPI
app = FastAPI()


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "port": PORT,
        "db_url_present": bool(DB_URL),
        "api_key_present": bool(FLIGHT_API_KEY),
        "mmbc_base_url": MMBC_BASE_URL
    }
