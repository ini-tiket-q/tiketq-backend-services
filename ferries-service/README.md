# Ferries Service

Ferries Service is one of the microservices in the **TiketQ** project, responsible for handling ferry-related data and operations.  
It is built with **FastAPI** and runs as a standalone container in Docker.

---

## 📋 Prerequisites

Before running this service, make sure you have:

- **Python 3.11** (if running without Docker)
- **Docker** & **Docker Compose** (recommended for faster setup)
- `.env` file at the project root containing the required environment variables

---

## ⚙️ Environment Configuration

Ferries Service reads configuration from the `.env` file located at the project root. Since there is no .env in the project, we have to create the file by copying .env.example

```bash
cp .env.example .env
```

## 🚀 How to Run
### 1️⃣ Run with Docker Compose (Recommended)

This service is already integrated into the root docker-compose.yml.
To start only the ferries service:

```bash
docker build -t ferries-service ./ferries-service
```

run the ferries-service container:
```bash
docker run -p 5001:8000 --env-file ./ferries-service/.env.example ferries-service
```

run postgres container:
```bash
docker-compose up -d postgres
```


### 2️⃣ Run Locally (Without Docker)
If you want to run directly on the host:

#### 1. Go to the ferries-service folder

```bash

cd ferries-service
```

#### 2. Create a virtual environment (optional but recommended)

```bash

python -m venv venv
source venv/bin/activate # Linux/Mac
venv\Scripts\activate # Windows
```
#### 3. Install dependencies

```bash
pip install --no-cache-dir -r requirements.txt
```

#### 4. Run the application with Uvicorn

```bash

uvicorn app:app --host 0.0.0.0 --port 8000
```

## 🔍 Checking Service Health

Once the ferries-service is running, you can check the health check endpoint:

```bash
curl http://localhost:5001/health
```
Sample response:

```json
{
"status": "ok",
"port": 5001,
"db_url_present": true,
"api_key_present": true
}
```
## 🔍 Basic Endpoints

Since the project doesn't have a real API yet, we'll use a mock API to simulate API calls.

The mock data is located in the ferries-service\adapters\external_api.py file:

```bash
def _mock_routes(self) -> List[FerryRoute]:
        return [
            FerryRoute(id="R1", origin="Tanjung Priok", destination="Pontianak", operator="Pelni"),
            FerryRoute(id="R2", origin="Surabaya", destination="Makassar", operator="Pelni"),
            FerryRoute(id="R3", origin="Batam", destination="Belawan", operator="ASDP"),
        ]
```

### 1. Get all routes
```bash
Get http://localhost:5001/ferries/routes
```

### 2. Get route by origin
```bash
Get http://localhost:5001/ferries/routes?origin={origin}
```
example:
```bash
Get http://localhost:5001/ferries/routes?origin=Surabaya
```

### 3. Get ferry schedules by route_id and 
```bash
Get http://localhost:5001/ferries/schedules?route_id={route_id}
```
example:
```bash
Get http://localhost:5001/ferries/schedules?route_id=R1
```

### 4. Get ferries booking
```bash
Get http://localhost:5001/ferries/bookings
```

### 5. Post booking
```bash
curl --location 'http://localhost:5001/ferries/bookings' \
--header 'Content-Type: application/json' \
--data-raw '{
    "schedule_id": "SR11",
    "passengers": [
        { "full_name": "Budi", "id_number": "12345" }
    ],
    "contact_email": "budi@example.com"
}'
```

### 6. Get booking by id
```bash
Get http://localhost:5001/ferries/bookings/{booking_id}
```


## 🗂 Folder Structure
```graphql
ferries-service/
│   .env.example        # Example environment file
│   app.py              # FastAPI entry point
│   requirements.txt    # Python dependencies
│   Dockerfile          # Docker build configuration
|   Readme
│
├───adapters
│       external_api.py # External ferry API integration
│
├───domain
│       models.py       # Data models
│       repository.py   # Database access
│       services.py     # Business logic
│
└───routes
        ferries.py      # API endpoints for ferry operations
```

## 🛠 Troubleshooting
Database connection failed
Make sure the postgres service in docker-compose.yml is running and the Secret Keys in .env is correct.

Port already in use
Change the PORT value in .env or adjust the --port parameter when starting Uvicorn.