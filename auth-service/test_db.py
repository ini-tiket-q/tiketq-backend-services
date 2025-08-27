from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env from root directory
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

print("AUTH_DB_URL:", os.getenv("AUTH_DB_URL"))

try:
    from adapters.db import engine
    print("Database connection successful!")
    
    # Test creating a table
    from adapters.db import Base
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    
except Exception as e:
    print(f"Error: {e}") 