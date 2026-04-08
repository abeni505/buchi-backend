# app/schemas/relations.py
from pydantic import BaseModel

class CustomerCreate(BaseModel):
    name: str
    phone: str

class AdoptionCreate(BaseModel):
    customer_id: str
    pet_id: str