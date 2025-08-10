from fastapi import FastAPI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Configuration from environment
PORT = int(os.getenv("PORT", 8000))
DB_URL = os.getenv("TRAINS_DB_URL")
KAI_API_KEY = os.getenv("KAI_API_KEY")
ENV = os.getenv("ENV", "development")

# Initialize FastAPI
app = FastAPI(
    title="Trains Service",
    description="Train booking and schedule service for TiketQ platform", 
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "trains-service",
        "port": PORT,
        "environment": ENV,
        "db_url_present": bool(DB_URL),
        "api_key_present": bool(KAI_API_KEY)
    }
