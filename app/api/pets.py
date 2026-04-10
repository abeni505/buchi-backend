# app/api/pets.py
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from app.schemas.pet import PetCreate
from app.core.database import db
from app.services.rescuegroups import fetch_external_pets
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
    return {"status": "success", "pet_id": pet_id}


# GET_PETS ENDPOINT:
@router.get("/get_pets")
async def get_pets(
    limit: int = Query(..., description="Required limit of results"),
    type: List[str] = Query(None, description="Multiple types allowed"),
    gender: List[str] = Query(None, description="Multiple genders allowed"),
    size: List[str] = Query(None, description="Multiple sizes allowed"),
    age: List[str] = Query(None, description="Multiple ages allowed"),
    good_with_children: Optional[bool] = None,
):
    # Build the dynamic search query for our local database
    local_query = {}
    if type:
        local_query["type"] = {"$in": type}
    if gender:
        local_query["gender"] = {"$in": gender}
    if size:
        local_query["size"] = {"$in": size}
    if age:
        local_query["age"] = {"$in": age}

    if good_with_children is not None:
        local_query["good_with_children"] = good_with_children

    # Fetch local pets FIRST (to prioritize them)
    cursor = db.client.buchi_db.pets.find(local_query).limit(limit)

    local_pets = await cursor.to_list(length=limit)

    formatted_results = []

    # Format local results to match the required response exactly
    for pet in local_pets:
        formatted_results.append(
            {
                "pet_id": pet["pet_id"],
                "source": "local",
                "type": pet["type"],
                "gender": pet["gender"],
                "size": pet["size"],
                "age": pet["age"],
                "good_with_children": pet.get("good_with_children", False),
                "Photos": pet.get("Photo", []),
            }
        )

    # Check if we still need more pets to reach the requested limit
    remaining_limit = limit - len(formatted_results)

    # If we need more, call the RescueGroups API
    if remaining_limit > 0:
        # Pass the exact same search filters, but only ask for the remaining amount
        external_params = {
            "limit": remaining_limit,
            "type": type,
            "gender": gender,
            "size": size,
            "age": age,
        }

        external_pets = await fetch_external_pets(external_params)

        # Format external results to match our system
        for epet in external_pets:
            # RescueGroups puts all the data inside an 'attributes' dictionary
            attr = epet.get("attributes", {})

            # Grab the thumbnail URL if it exists
            photos = []
            if attr.get("pictureThumbnailUrl"):
                photos.append(attr.get("pictureThumbnailUrl"))

            fallback_type = type[0] if type else "Unknown"

            pet_type = attr.get("speciesString") or fallback_type
            pet_size = attr.get("sizeGroup") or "Unknown"
            pet_age = attr.get("ageGroup") or "Unknown"
            pet_gender = attr.get("sex") or "Unknown"

            formatted_results.append(
                {
                    "pet_id": str(epet.get("id")),
                    "source": "rescuegroups",
                    "type": pet_type,
                    "gender": pet_gender,
                    "size": pet_size,
                    "age": pet_age,
                    "good_with_children": attr.get("isGoodWithChildren", False),
                    "Photos": photos,
                }
            )

    # Return the perfectly combined list
    return {"status": "success", "pets": formatted_results}


# GET PET DETAILS ENDPOINT:
@router.get("/get_pets/{pet_id}")
async def get_pet_details(pet_id: str):
    """Fetch the full details of a single pet by ID."""

    # Check if the pet is in our local database
    local_pet = await db.client.buchi_db.pets.find_one({"pet_id": pet_id})

    if local_pet:
        return {
            "status": "success",
            "pet": {
                "pet_id": local_pet["pet_id"],
                "source": "local",
                "type": local_pet.get("type"),
                "gender": local_pet.get("gender"),
                "size": local_pet.get("size"),
                "age": local_pet.get("age"),
                "good_with_children": local_pet.get("good_with_children", False),
                "Photos": local_pet.get("Photo", []),
            },
        }

    # If not found locally, check RescueGroups API
    from app.services.rescuegroups import get_external_pet_by_id

    external_pet = await get_external_pet_by_id(pet_id)

    if external_pet:
        attr = external_pet.get("attributes", {})

        photos = []
        if attr.get("pictureThumbnailUrl"):
            photos.append(attr.get("pictureThumbnailUrl"))

        return {
            "status": "success",
            "pet": {
                "pet_id": str(external_pet.get("id")),
                "source": "rescuegroups",
                "type": attr.get("speciesString", "Unknown"),
                "gender": attr.get("sex", "Unknown"),
                "size": attr.get("sizeGroup", "Unknown"),
                "age": attr.get("ageGroup", "Unknown"),
                "good_with_children": attr.get("isGoodWithChildren", False),
                "Photos": photos,
            },
        }

    # If neither database has it, return a 404
    raise HTTPException(status_code=404, detail="Pet not found")
