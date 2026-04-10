# app/api/adoptions.py
from fastapi import APIRouter, HTTPException
from app.schemas.relations import AdoptionCreate
from app.core.database import db
from app.services.rescuegroups import get_external_pet_by_id
import uuid
from datetime import datetime, timedelta

router = APIRouter()


@router.post("/adopt", status_code=201)
async def adopt(adoption: AdoptionCreate):
    # 1. Verify the Customer exists locally
    customer = await db.client.buchi_db.customers.find_one(
        {"customer_id": adoption.customer_id}
    )
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # 2. Verify the Pet exists (Check local DB first)
    pet = await db.client.buchi_db.pets.find_one({"pet_id": adoption.pet_id})

    if pet:
        pet_type = pet.get("type")
        pet_gender = pet.get("gender")
        pet_size = pet.get("size")
        pet_age = pet.get("age")
        good_with_children = pet.get("good_with_children")
    else:
        # If not local, verify it exists on RescueGroups
        external_pet = await get_external_pet_by_id(adoption.pet_id)
        if not external_pet:
            raise HTTPException(
                status_code=404, detail="Pet not found locally or externally"
            )

        attr = external_pet.get("attributes", {})
        pet_type = attr.get("speciesString")
        pet_gender = attr.get("sex")
        pet_size = attr.get("sizeGroup")
        pet_age = attr.get("ageGroup")
        good_with_children = attr.get("isGoodWithChildren", False)

    # 3. Create the combined Adoption Record
    adoption_id = str(uuid.uuid4())
    record = {
        "adoption_id": adoption_id,
        "customer_id": customer["customer_id"],
        "customer_name": customer["name"],
        "customer_phone": customer["phone"],
        "pet_id": adoption.pet_id,
        "type": pet_type,
        "gender": pet_gender,
        "size": pet_size,
        "age": pet_age,
        "good_with_children": good_with_children,
        "request_date": datetime.utcnow(),
    }

    await db.client.buchi_db.adoptions.insert_one(record)

    return {"status": "success", "adoption_id": adoption_id}


@router.get("/get_adoption_requests")
async def get_adoption_requests(from_date: str, to_date: str):

    # Parse the date strings
    try:
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        # Add hours to 'to_date' to include the entire final day in the search
        to_dt = datetime.strptime(to_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")

    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

    # Fetch all records within the date range
    cursor = db.client.buchi_db.adoptions.find(
        {"request_date": {"$gte": from_dt, "$lte": to_dt}}
    )
    records = await cursor.to_list(length=1000)

    # Dictionaries to hold our aggregated data
    adopted_pet_types = {}
    weekly_adoption_requests = {}

    for r in records:
        # 1. Count by Pet Type
        pet_type = r.get("type", "Unknown")
        # If the type exists, add 1. If not, start it at 1.
        adopted_pet_types[pet_type] = adopted_pet_types.get(pet_type, 0) + 1

        # 2. Group by Week (Using the Monday of each request's week as the key)
        req_date = r["request_date"]
        # Subtract the weekday number to always get back to Monday
        monday_of_week = req_date - timedelta(days=req_date.weekday())
        week_str = monday_of_week.strftime("%Y-%m-%d")

        weekly_adoption_requests[week_str] = (
            weekly_adoption_requests.get(week_str, 0) + 1
        )

    # Return the exact JSON structure requested by the documentation
    return {
        "status": "success",
        "data": {
            "adopted_pet_types": adopted_pet_types,
            "weekly_adoption_requests": weekly_adoption_requests,
        },
    }
