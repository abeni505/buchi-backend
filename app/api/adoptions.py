# app/api/adoptions.py
from fastapi import APIRouter, HTTPException, Query
from app.schemas.relations import (
    AdoptionCreate,
    AdoptionResponse,
    AdoptionListResponse,
    ReportResponse,
)
from app.core.database import db
from app.services.rescuegroups import get_external_pet_by_id
import uuid
from datetime import date, datetime, timedelta, timezone, time

router = APIRouter()


@router.post(
    "/adopt",
    response_model=AdoptionResponse,
    status_code=201,
    tags=["Adoptions"],
    summary="Submit an Adoption Request",
)
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
        "request_date": datetime.now(timezone.utc),
    }

    await db.client.buchi_db.adoptions.insert_one(record)

    return {"status": "success", "adoption_id": adoption_id}


@router.get(
    "/get_adoption_requests", response_model=AdoptionListResponse, tags=["Adoptions"]
)
async def get_adoption_requests(
    from_date: date = Query(..., examples=["2026-04-01"]),
    to_date: date = Query(..., examples=["2026-04-10"]),
):
    # Convert to datetime objects for MongoDB range queries
    from_dt = datetime.combine(from_date, time.min)
    to_dt = datetime.combine(to_date, time.max)

    pipeline = [
        # 1. Filter by date range
        {"$match": {"request_date": {"$gte": from_dt, "$lte": to_dt}}},
        # 2. Sort by date: 1 = Ascending (Oldest first/top)
        {"$sort": {"request_date": 1}},
        # 3. Join with Customers
        {
            "$lookup": {
                "from": "customers",
                "localField": "customer_id",
                "foreignField": "customer_id",
                "as": "customer",
            }
        },
        # 4. Join with Pets
        {
            "$lookup": {
                "from": "pets",
                "localField": "pet_id",
                "foreignField": "pet_id",
                "as": "pet",
            }
        },
        # 5. Flatten the arrays created by lookup
        {"$unwind": "$customer"},
        {"$unwind": "$pet"},
    ]

    cursor = db.client.buchi_db.adoptions.aggregate(pipeline)
    adoptions = await cursor.to_list(length=1000)

    formatted_data = []
    for r in adoptions:
        formatted_data.append(
            {
                "customer_id": r["customer_id"],
                "customer_name": r["customer"].get("name"),
                "customer_phone": r["customer"].get("phone"),
                "pet_name": r["pet"].get("pet_name"),
                "pet_id": r["pet_id"],
                "type": r["pet"].get("type"),
                "gender": r["pet"].get("gender"),
                "size": r["pet"].get("size"),
                "age": r["pet"].get("age"),
                "good_with_children": r["pet"].get("good_with_children", False),
            }
        )

    return {"status": "success", "data": formatted_data}


@router.get(
    "/get_adoption_report",
    response_model=ReportResponse,
    tags=["Adoptions"],
    summary="Get Adoption Statistics Report",
)
async def get_adoption_report(
    start_date: date = Query(
        ...,
        description="The start date for the report in YYYY-MM-DD format",
        example="2026-01-01",  # This shows up in Swagger!
    ),
    end_date: date = Query(
        ...,
        description="The end date for the report in YYYY-MM-DD format",
        example="2026-04-10",
    ),
):

    # Convert date to datetime for MongoDB comparison
    # from_dt starts at 00:00:00
    from_dt = datetime.combine(start_date, time.min)
    # to_dt ends at 23:59:59
    to_dt = datetime.combine(end_date, time.max)

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
            "report_period": {"from": from_dt, "to": to_dt},
            "adopted_pet_types": adopted_pet_types,
            "weekly_adoption_requests": weekly_adoption_requests,
            "total_requests": len(records),
        },
    }
