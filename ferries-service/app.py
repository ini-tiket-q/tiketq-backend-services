from fastapi import FastAPI
from dotenv import load_dotenv
import os

from routes.ferries import router as ferries_router
from routes.ferries_mock import router_mock as ferries_router_mock

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
app.include_router(ferries_router_mock)




# from fastapi import FastAPI
# from dotenv import load_dotenv
# import os

# from routes.ferries import router as ferries_router

# # Load .env variables (This line is kept, but it won't find the .env file
# # inside the container unless it's explicitly copied)
# load_dotenv()

# # Load config from env, provide default values if not found.
# # Docker won't expose variables from the .env file here, so default values are necessary.
# PORT = int(os.getenv("PORT", 8000)) 
# DB_URL = os.getenv("FERRIES_DB_URL", "postgresql://user:password@db_host:5432/db_name") # Contoh: ganti dengan URL DB yang sesuai
# FERRY_API_KEY = os.getenv("EXTERNAL_FERRIES_API_KEY", "your_default_api_key") # Contoh: ganti dengan kunci API default

# # Initialize FastAPI
# app = FastAPI(title="Ferries Service API")

# @app.get("/health")
# def health_check():
#     return {
#         "status": "ok",
#         "port": PORT,
#         "db_url_present": bool(DB_URL),
#         "api_key_present": bool(FERRY_API_KEY)
#     }

# app.include_router(ferries_router)