from fastapi import FastAPI
from dotenv import load_dotenv
from pathlib import Path
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
MMBC_BASE_URL = os.getenv("MMBC_BASE_URL")



# ✅ FastAPI App
app = FastAPI(
    title="tiketQ Flights/Flight-Service",
    docs_url="/docs",
    openapi_url="/openapi.json",
    servers=[{"url": "http://localhost:5001"}]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(flights_router, prefix="/api/v1/json", tags=["flights"])
app.include_router(bookings_router, prefix="/api/v1", tags=["payments"])


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "port": PORT,
        "db_url_present": bool(DB_URL),
        "api_key_present": bool(FLIGHT_API_KEY),
        "mmbc_base_url": MMBC_BASE_URL
    }
