from fastapi import FastAPI
from dotenv import load_dotenv
from routes import routes_flights
import os

# Load .env variables
load_dotenv()

# Load config from env
PORT = int(os.getenv("PORT", 5001))
DB_URL = os.getenv("FLIGHTS_DB_URL")
FLIGHT_API_KEY = os.getenv("EXTERNAL_FLIGHT_API_KEY")

# Initialize FastAPI
app = FastAPI()

# Register routes
app.include_router(routes_flights)
print("✅ Routes flights registered")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "port": PORT,
        "db_url_present": bool(DB_URL),
        "api_key_present": bool(FLIGHT_API_KEY),
    }
