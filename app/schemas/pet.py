# app/schemas/pet.py
from pydantic import BaseModel
from typing import List


class PetCreate(BaseModel):
    pet_name: str
    type: str
    gender: str
    size: str
    age: str
    good_with_children: bool
    Photos: List[str] = []
