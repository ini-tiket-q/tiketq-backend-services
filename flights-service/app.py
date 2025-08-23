import os
from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from routes import routes_flights
from routes import routes_bookings

# ✅ Force load from root .env
load_dotenv(dotenv_path=Path('.') / ".env")

# ✅ Confirm these are loaded
PORT = int(os.getenv("PORT", 5001))
DB_URL = os.getenv("FLIGHTS_DB_URL")
FLIGHT_API_KEY = os.getenv("EXTERNAL_FLIGHT_API_KEY")

# Initialize FastAPI
app = FastAPI()

app.include_router(routes_flights,  prefix="/api/v1/flights")
app.include_router(routes_bookings.router, prefix="/api/v1/bookings")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "port": PORT,
        "db_url_present": bool(DB_URL),
        "api_key_present": bool(FLIGHT_API_KEY),
        "mmbc_base_url": os.getenv("MMBC_BASE_URL")
    }
