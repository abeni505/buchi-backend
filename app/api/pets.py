# app/api/pets.py
from fastapi import APIRouter
from app.schemas.pet import PetCreate
from app.core.database import db
import uuid

router = APIRouter()

@router.post("/create_pet", status_code=201)
async def create_pet(pet: PetCreate):
    # Convert the Pydantic model to a dictionary
    pet_dict = pet.model_dump() 
    
    # Generate a unique pet_id
    pet_id = str(uuid.uuid4())
    pet_dict["pet_id"] = pet_id
    
    # Insert the pet into the local MongoDB 'pets' collection
    await db.client.buchi_db.pets.insert_one(pet_dict)
    
    # Return the required response format
    return {
        "status": "success",
        "pet_id": pet_id
    }