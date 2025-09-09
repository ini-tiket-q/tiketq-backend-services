import os
from dotenv import load_dotenv
from pathlib import Path

# Prefer .env, fallback to .env.example
env_file = ".env" if (Path(__file__).resolve().parent / ".env").exists() else ".env.example"
env_path = Path(__file__).resolve().parent / env_file
load_dotenv(dotenv_path=env_path)

print(f"🔧 Loaded from {env_file}")

MOCK_REMOTE = os.getenv("MOCK_REMOTE", "False").lower() == "true"
PORT = int(os.getenv("PORT", 5001))
DB_URL = os.getenv("FLIGHTS_DB_URL")
FLIGHT_API_KEY = os.getenv("EXTERNAL_FLIGHT_API_KEY")
