from fastapi import FastAPI
from dotenv import load_dotenv
import os
from routes.dashboard import router as dashboard_router

# Load .env variables
load_dotenv()


# Load config from env
PORT = int(os.getenv("PORT", 8000))
DB_URL = os.getenv("FERRIES_DB_URL")
FERRY_API_KEY = os.getenv("EXTERNAL_FERRIES_API_KEY")

# Initialize FastAPI
app = FastAPI(title="Ferries Service API")

app.include_router(dashboard_router, prefix="/ferry")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "port": PORT,
        "db_url_present": bool(DB_URL),
        "api_key_present": bool(FERRY_API_KEY)
    }
    
@app.get("/")
def root():
    return {"status": "ok", "service": "Ferries Service"}