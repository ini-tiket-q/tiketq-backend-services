# config.py
import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(".") / ".env")

MOCK_REMOTE = os.getenv("MOCK_REMOTE", "False").lower() == "true"
PORT = int(os.getenv("PORT", 5001))
DB_URL = os.getenv("FLIGHTS_DB_URL")
FLIGHT_API_KEY = os.getenv("EXTERNAL_FLIGHT_API_KEY")
