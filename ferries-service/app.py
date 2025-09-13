import sys
from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
import os
from routes.ferries import router as ferries_router
# from routes.ferries_mock import router_mock as ferries_router_mock
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Load .env variables
load_dotenv()

# Load config from env
PORT = int(os.getenv("PORT", 8000))
DB_URL = os.getenv("FERRIES_DB_URL")
FERRY_API_KEY = os.getenv("EXTERNAL_FERRIES_API_KEY")

# Initialize FastAPI
app = FastAPI(
    title="Ferries Service",
    description="Ferry booking service for TiketQ platform",
    version="1.0.0"
)

app.include_router(ferries_router, prefix="/api/v1/ferries")
# app.include_router(ferries_router_mock)


health_router = APIRouter(prefix="/ferries")

@app.get("/")
async def root():
    return {"service": "Ferries Service", "status": "running", "version": "1.0.0"}

# @app.get("/health")
@health_router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "port": PORT,
        "db_url_present": bool(DB_URL),
        "api_key_present": bool(FERRY_API_KEY)
    }

app.include_router(health_router, prefix="/api/v1/ferries")  # ✅ Important



