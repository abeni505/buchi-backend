# Buchi Pet Adoption API 🐾

A production-ready FastAPI backend for the Buchi Pet Adoption System. This system allows shelter administrators to manage customer registrations, search a unified database of local and external pets, process adoptions, and generate analytical reports.

**Postman API Documentation:** https://documenter.getpostman.com/view/37344301/2sBXitCSan

## Features
* **Hybrid Search:** Prioritizes local MongoDB records with a seamless fallback to the external RescueGroups API.
* **Production Server:** Containerized and served via Gunicorn with Uvicorn workers.
* **Robust Testing:** 100% test coverage for all endpoints including unhappy paths (404, 422, 400 errors) using Pytest and mock integrations.

---

## 🚀 How to Run the Application (Docker)

This application is fully containerized. You do not need Python installed on your local machine to run it.

### 1. Clone the repository
```bash
git clone https://github.com/abeni505/buchi-backend
cd buchi-backend
```

### 2. Configure Environment Variables
Rename the `.env.example` file to `.env` and insert your RescueGroups API key:

```bash
cp .env.example .env
```

### 3. Start the System
Run the following command to build the image and launch the FastAPI server alongside the MongoDB database:

```bash
docker-compose up --build
```
### 4. Access the API
Once the containers are running, you can access the interactive Swagger documentation at:


Swagger UI: http://127.0.0.1:8000/docs 

ReDoc UI: http://127.0.0.1:8000/redoc


## 🧪 How to Run the Unit Tests
If you wish to run the test suite locally (without Docker), ensure you have Python 3.12+ installed.
### 1. Set up the environment
Activate your virtual environment and install the required dependencies:
```bash
pip install -r requirements.txt
pip install pytest httpx
```

### 2. Run the test suite
Execute Pytest to run the full end-to-end integration and negative test suite:
```bash
python -m pytest
```



# ‍💻 Author

Abenezer M. Woldesenbet 