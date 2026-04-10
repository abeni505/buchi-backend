# app/api/pets.py
from fastapi import APIRouter, Query
from typing import Optional
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
    type: Optional[str] = None,
    gender: Optional[str] = None,
    size: Optional[str] = None,
    age: Optional[str] = None,
    good_with_children: Optional[bool] = None,
):
    # Build the dynamic search query for our local database
    query = {}
    if type:
        query["type"] = type
    if gender:
        query["gender"] = gender
    if size:
        query["size"] = size
    if age:
        query["age"] = age
    if good_with_children is not None:
        query["good_with_children"] = good_with_children

    # Fetch local pets FIRST (to prioritize them)
    cursor = db.client.buchi_db.pets.find(query).limit(limit)
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
        external_params = query.copy()
        external_params["limit"] = remaining_limit

        external_pets = await fetch_external_pets(external_params)

        # Format external results to match our system
        for epet in external_pets:
            # RescueGroups puts all the data inside an 'attributes' dictionary
            attr = epet.get("attributes", {})

            # Grab the thumbnail URL if it exists
            photos = []
            if attr.get("pictureThumbnailUrl"):
                photos.append(attr.get("pictureThumbnailUrl"))

            formatted_results.append(
                {
                    "pet_id": str(epet.get("id")),
                    "source": "rescuegroups",  # Updated source tag
                    "type": attr.get("speciesString")
                    or external_params.get("type")
                    or "Unknown",
                    "gender": attr.get("sex"),
                    "size": attr.get("sizeGroup"),
                    "age": attr.get("ageGroup"),
                    "good_with_children": attr.get("isGoodWithChildren", False),
                    "Photos": photos,
                }
            )

    # Return the perfectly combined list
    return {"status": "success", "pets": formatted_results}
