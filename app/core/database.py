# # app/core/database.py

import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()


class Database:
    client: AsyncIOMotorClient = None


# We create ONE instance here
db = Database()


async def connect_to_mongo():
    mongo_url = os.getenv("MONGO_URL")
    if not mongo_url:
        print("❌ DB Error: MONGO_URL is missing from environment variables!")
        return

    try:
        # Assign the client to the singleton instance
        db.client = AsyncIOMotorClient(mongo_url)
        # Verify connection
        await db.client.admin.command("ping")
        print("✅ Successfully connected to MongoDB Atlas!")
    except Exception as e:
        print(f"❌ MongoDB Connection Failed: {e}")
        db.client = None


async def close_mongo_connection():
    if db.client:
        db.client.close()
        print("DB connection closed.")
