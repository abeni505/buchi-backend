# app/api/customers.py
from fastapi import APIRouter
from app.schemas.relations import CustomerCreate
from app.core.database import db
import uuid

router = APIRouter()

@router.post("/add_customer", status_code=201)
async def add_customer(customer: CustomerCreate):
    # 1. Check if the phone number already exists in the database
    existing_customer = await db.client.buchi_db.customers.find_one({"phone": customer.phone})
    
    if existing_customer:
        # If found, return the existing customer_id
        return {
            "status": "success",
            "customer_id": existing_customer["customer_id"]
        }
    
    # 2. If it does not exist, create a new customer record
    customer_id = str(uuid.uuid4())
    customer_dict = customer.model_dump()
    customer_dict["customer_id"] = customer_id
    
    await db.client.buchi_db.customers.insert_one(customer_dict)
    
    return {
        "status": "success",
        "customer_id": customer_id
    }