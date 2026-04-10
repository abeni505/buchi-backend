# app/schemas/relations.py
from pydantic import BaseModel, Field


class CustomerCreate(BaseModel):
    name: str = Field(
        ...,
        description="The full legal name of the adopter.",
        examples=["Abenezer Woldesenbet"],
    )
    phone: str = Field(
        ...,
        description="Phone number including country code.",
        examples=["+251911223344"],
    )


class CustomerResponse(BaseModel):
    customer_id: str = Field(
        ..., description="The unique ID generated for the customer."
    )
    name: str
    phone: str


class AdoptionCreate(BaseModel):
    customer_id: str = Field(
        ...,
        description="The UUID of the registered customer.",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    pet_id: str = Field(
        ...,
        description="The ID of the pet (local UUID or RescueGroups integer).",
        examples=["9999"],
    )


class AdoptionResponse(BaseModel):
    adoption_id: str = Field(..., description="The unique ID for the adoption request.")
    customer_id: str
    pet_id: str
    status: str = Field("Pending", description="The current status of the adoption.")
