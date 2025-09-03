import os
from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from routes import routes_flights
from routes import routes_bookings
from config import MOCK_REMOTE, PORT, DB_URL, FLIGHT_API_KEY

# ✅ Force load from root .env


# Initialize FastAPI
app = FastAPI()
print(f"🧪 MOCK MODE: {MOCK_REMOTE}")


app.include_router(routes_flights, prefix="/api/v1/flights")
app.include_router(routes_bookings.router, prefix="/api/v1/bookings")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "port": PORT,
        "db_url_present": bool(DB_URL),
        "api_key_present": bool(FLIGHT_API_KEY),
        "mmbc_base_url": os.getenv("MMBC_BASE_URL"),
    }
