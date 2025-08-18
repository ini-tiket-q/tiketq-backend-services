from fastapi import FastAPI
from dotenv import load_dotenv
import os
from routes.flights import router as flights_router
from routes.payments import router as payments_router

# Load .env variables
load_dotenv()

# Load config from env
PORT = int(os.getenv("PORT", 5001))
DB_URL = os.getenv("FLIGHTS_DB_URL")
FLIGHT_API_KEY = os.getenv("EXTERNAL_FLIGHT_API_KEY")

# Initialize FastAPI
app = FastAPI(title="tiketQ Flights/Payments Service")
app.include_router(flights_router, prefix="/json", tags=["flights"])
app.include_router(payments_router, prefix="/json", tags=["payments"])


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "port": PORT,
        "db_url_present": bool(DB_URL),
        "api_key_present": bool(FLIGHT_API_KEY),
    }
