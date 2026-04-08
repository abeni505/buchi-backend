# app/services/rescuegroups.py
import httpx
from typing import Dict, Any
from app.core.config import settings

async def fetch_external_pets(params: Dict[str, Any]) -> list:
    """
    Fetches pets from RescueGroups API v5 using dynamic filters.
    """
    url = "https://api.rescuegroups.org/v5/public/animals/search/available"
    headers = {
        "Authorization": settings.RESCUE_GROUPS_API_KEY,
        "Content-Type": "application/vnd.api+json"
    }
    
    # 1. Translate Buchi parameters to RescueGroups filters
    filters = []
    if params.get("type"):
        # RescueGroups expects "Dog" or "Cat" capitalized
        filters.append({"fieldName": "species.singular", "operation": "equals", "criteria": params.get("type").capitalize()})
    if params.get("gender"):
        filters.append({"fieldName": "animals.sex", "operation": "equals", "criteria": params.get("gender").capitalize()})
    if params.get("size"):
        filters.append({"fieldName": "animals.sizeGroup", "operation": "equals", "criteria": params.get("size").capitalize()})
    if params.get("age"):
        filters.append({"fieldName": "animals.ageGroup", "operation": "equals", "criteria": params.get("age").capitalize()})
    
    payload = {
        "data": {
            "filters": filters
        }
    }
    
    # RescueGroups accepts 'limit' as a URL query parameter
    query_params = {"limit": params.get("limit", 20)}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, params=query_params)
            response.raise_for_status()
            
            # RescueGroups stores the array of pets inside a 'data' object
            return response.json().get("data", [])
    except Exception as e:
        print(f"RescueGroups API Error: {e}")
        return []

async def get_external_pet_by_id(pet_id: str) -> dict:
    """Fetches a single pet by ID to verify it exists during adoption."""
    url = f"https://api.rescuegroups.org/v5/public/animals/{pet_id}"
    headers = {
        "Authorization": settings.RESCUE_GROUPS_API_KEY,
        "Content-Type": "application/vnd.api+json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json().get("data", [])
                if data:
                    return data[0]
    except Exception:
        return None
    return None