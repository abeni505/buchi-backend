# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.database import connect_to_mongo, close_mongo_connection
from app.api import pets, customers, adoptions


# This lifecycle manager handles connecting/disconnecting from the DB
@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Buchi Pet Adoption API",
    description="""
    Welcome to the Buchi Pet Adoption System API.
    
    This API allows shelter administrators and frontend applications to:
    * **Manage Customers:** Register new adopters.
    * **Search Pets:** Filter through local and external shelter databases.
    * **Process Adoptions:** Securely link customers to pets.
    * **Generate Reports:** View statistical adoption data.
    """,
    version="1.0.0",
)

app.include_router(pets.router)
app.include_router(customers.router)
app.include_router(adoptions.router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Buchi API!"}
