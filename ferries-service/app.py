from fastapi import FastAPI

from dotenv import load_dotenv
import os

# Load .env variables
load_dotenv()

# Load config from env
PORT = int(os.getenv("PORT", 5001))
DB_URL = os.getenv("FERRYS_DB_URL")
FERRY_API_KEY = os.getenv("EXTERNAL_FERRY_API_KEY")

# Initialize FastAPI
app = FastAPI(
    title="Ferries Service",
    description="Ferry booking service for TiketQ platform",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"service": "Ferries Service", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return return {
        "status": "ok",
        "port": PORT,
        "db_url_present": bool(DB_URL),
        "api_key_present": bool(FERRY_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000)

