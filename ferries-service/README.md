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


### Post booking

```bash
POST http://localhost:5001/ferries/book
```

Example:
```bash
curl --location 'http://localhost:5001/ferries/book' \
--header 'Content-Type: application/json' \
--data-raw '{
    "schedule_id": "SCH003",
    "passengers": [
        {
        "type": "Adult",
        "title": "Mr",
        "name": "Yusuf Johan",
        "passport_no": "A1234565",
        "nationality": "ID",
        "issuing_country": "Indonesia",
        "dob": "1999-05-21",
        "passport_expiry": "2030-05-21",
        "passport_issue": "2020-05-21"
        },
        {
        "type": "Adult",
        "title": "Miss",
        "name": "Siti",
        "passport_no": "B7654321",
        "nationality": "ID",
        "issuing_country": "Indonesia",
        "dob": "2015-02-10",
        "passport_expiry": "2030-02-10",
        "passport_issue": "2020-02-10"
        }
        
    ],
    "requirements": {
        "email": "yusuf@mail.com",
        "confirm_email": "yusuf@mail.com",
        "mobile_phone": "08123456666",
        "whatsapp_no": "628123456666"
    }
}'
```
Response:
```bash
{
    "booking_id": "587dde66-c892-47a9-ab71-f6b8540a98c8",
    "status": "incomplete",
    "total_price": 340000.0,
    "message": "Booking created. Transaction ID: 357885ed-d81e-420a-9b70-b461c444a390"
}
```

### Get Transactions
```bash
GET http://localhost:5001/ferries/transactions
```
Response:
```bash
[
    {
        "transaction_id": "357885ed-d81e-420a-9b70-b461c444a390",
        "booking_id": "587dde66-c892-47a9-ab71-f6b8540a98c8",
        "amount": 340000,
        "status": "pending"
    }
]
```

### Update Transaction Status
```bash
PUT http://localhost:5001/ferries/transactions/{transaction_id}?status=<new_status>
```
Example:
```bash
http://localhost:5001/ferries/transactions/699b87e1-ac15-495c-99b0-8fcf572eb3d0?status=paid
```
Response:
```bash
{
    "transaction_id": "357885ed-d81e-420a-9b70-b461c444a390",
    "booking_id": "587dde66-c892-47a9-ab71-f6b8540a98c8",
    "amount": 340000,
    "status": "paid"
}
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