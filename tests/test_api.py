# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app


# This fixture forces the DB to connect before testing
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


state = {}


# we  pass 'client' as an argument to every test function
def test_1_root(client):
    """1. Test if the API boots up correctly."""
    response = client.get("/")
    assert response.status_code == 200


def test_2_create_customer(client):
    """2. Test customer registration."""
    response = client.post(
        "/add_customer",
        json={"name": "Integration Test User", "phone": "+251999000111"},
    )
    assert response.status_code == 201
    state["customer_id"] = response.json()["customer_id"]


def test_3_get_customers(client):
    """3. Test the admin customer list."""
    response = client.get("/get_customers")
    assert response.status_code == 200
    assert isinstance(response.json()["customers"], list)


def test_4_create_pet(client):
    """4. Test local pet creation."""
    response = client.post(
        "/create_pet",
        json={
            "type": "Dog",
            "gender": "Male",
            "size": "Medium",
            "age": "Young",
            "good_with_children": True,
            "Photo": ["http://example.com/test-dog.jpg"],
        },
    )
    assert response.status_code == 201
    state["pet_id"] = response.json()["pet_id"]


@patch("app.api.pets.fetch_external_pets", new_callable=AsyncMock)
def test_5_get_pets(mock_fetch, client):
    """5. Test the search endpoint (mocking the external API)."""
    mock_fetch.return_value = []
    response = client.get("/get_pets?limit=10&type=Dog")
    assert response.status_code == 200
    assert isinstance(response.json()["pets"], list)


def test_6_get_pet_details(client):
    """6. Test viewing a specific pet's profile."""
    pet_id = state.get("pet_id")
    response = client.get(f"/get_pets/{pet_id}")
    assert response.status_code == 200
    assert response.json()["pet"]["pet_id"] == pet_id


def test_7_adopt_pet(client):
    """7. Test the adoption workflow using the IDs we just created."""
    response = client.post(
        "/adopt",
        json={"customer_id": state.get("customer_id"), "pet_id": state.get("pet_id")},
    )
    assert response.status_code == 201
    assert "adoption_id" in response.json()


def test_8_get_adoption_requests(client):
    """8. Test the aggregated statistical reporting endpoint."""
    response = client.get(
        "/get_adoption_requests?from_date=2020-01-01&to_date=2030-01-01"
    )
    assert response.status_code == 200
    data = response.json()
    assert "adopted_pet_types" in data["data"]
    assert "weekly_adoption_requests" in data["data"]


# --- NEGATIVE TESTS (UNHAPPY PATHS) ---


def test_9_adopt_pet_fake_customer(client):
    """9. NEGATIVE TEST: Trying to adopt with a fake customer ID."""
    response = client.post(
        "/adopt",
        json={"customer_id": "this-is-a-fake-id", "pet_id": state.get("pet_id")},
    )
    # We purposefully EXPECT a failure code (404)
    assert response.status_code == 404
    # We EXPECT our custom error message
    assert response.json()["detail"] == "Customer not found"


@patch("app.services.rescuegroups.get_external_pet_by_id", new_callable=AsyncMock)
def test_10_get_pet_details_not_found(mock_get_external, client):
    """10. NEGATIVE TEST: Fetch a pet that doesn't exist locally or externally."""
    # Force the mocked RescueGroups API to return None
    mock_get_external.return_value = None

    response = client.get("/get_pets/fake-pet-id-999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Pet not found"


def test_11_adopt_fake_customer(client):
    """11. NEGATIVE TEST: Try to adopt a pet using a non-existent customer ID."""
    response = client.post(
        "/adopt",
        json={"customer_id": "definitely-not-a-real-id", "pet_id": state.get("pet_id")},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_12_create_pet_missing_field(client):
    """12. NEGATIVE TEST: Try to create a pet but forget a required field."""
    # We are intentionally leaving out the required 'type' field
    response = client.post(
        "/create_pet",
        json={
            "gender": "Male",
            "size": "Medium",
            "age": "Young",
            "good_with_children": True,
        },
    )
    # 422 Unprocessable Entity is FastAPI's automatic validation error
    assert response.status_code == 422
    assert "detail" in response.json()


def test_13_invalid_date_format(client):
    """13. NEGATIVE TEST: Pass a poorly formatted date to the report endpoint."""
    response = client.get(
        "/get_adoption_requests?from_date=April-8th&to_date=2026-04-08"
    )
    assert response.status_code == 400
    assert "Invalid date format" in response.json()["detail"]
