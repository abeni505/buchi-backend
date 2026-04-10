# app/schemas/relations.py
from pydantic import BaseModel, Field
from datetime import date
from typing import List, Dict, Any


class CustomerCreate(BaseModel):
    name: str = Field(
        ...,
        description="The full legal name of the adopter.",
        examples=["user1"],
    )
    phone: str = Field(
        ...,
        description="Phone number including country code.",
        examples=["+251911223344"],
    )


class CustomerResponse(BaseModel):
    status: str
    customer_id: str


class AdoptionCreate(BaseModel):
    customer_id: str = Field(
        ...,
        description="The UUID of the registered customer.",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    pet_id: str = Field(
        ...,
        description="The ID of the pet (local UUID or RescueGroups integer).",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )


class AdoptionResponse(BaseModel):
    status: str = Field("Pending", description="The current status of the adoption.")
    adoption_id: str = Field(..., description="The unique ID for the adoption request.")


class AdoptionListEntry(BaseModel):
    customer_id: str
    customer_name: str
    customer_phone: str
    pet_id: str
    pet_name: str
    type: str
    gender: str
    size: str
    age: str
    good_with_children: bool


class AdoptionListResponse(BaseModel):
    status: str = "success"
    data: List[AdoptionListEntry]


class ReportRequest(BaseModel):
    from_date: date = Field(
        ..., description="Start date in YYYY-MM-DD format", examples=["2022-02-01"]
    )
    to_date: date = Field(
        ..., description="End date in YYYY-MM-DD format", examples=["2022-03-01"]
    )


class ReportResponse(BaseModel):
    status: str = "success"
    data: Dict[str, Any]
