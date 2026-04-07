# app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # This defaults to a local MongoDB instance
    MONGO_URL: str = os.getenv("MONGO_URL", "mongodb://localhost:27017")
    DATABASE_NAME: str = "buchi_db"

settings = Settings()