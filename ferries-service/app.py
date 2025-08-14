from fastapi import FastAPI
from dotenv import load_dotenv
import os

from routes.ferries import router as ferries_router

# Load .env variables
load_dotenv()

# Load config from env
PORT = int(os.getenv("PORT", 5001))
DB_URL = os.getenv("FERRIES_DB_URL")
FERRY_API_KEY = os.getenv("EXTERNAL_FERRIES_API_KEY")

# Initialize FastAPI
app = FastAPI(title="Ferries Service API")

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "port": PORT,
        "db_url_present": bool(DB_URL),
        "api_key_present": bool(FERRY_API_KEY)
    }

app.include_router(ferries_router)