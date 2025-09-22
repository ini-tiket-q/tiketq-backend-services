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
To start the containers:

```bash
docker-compose up -d --build
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
curl http://localhost:8003/health
```
Sample response:

```json
{
"status": "ok",
"port": 8003,
"db_url_present": true,
"api_key_present": true
}
```
## 🔍 Basic Endpoints

This project use real APIs provided by Sindo Ferry to create, display, update, and delete data

### Agen Login (Mandatory)
```bash
POST https://api.test.sindoferry.com.sg/agent/Agent/Login
```
Request Body:
```json
{
  "agentCode": "T900T63",
  "username": "testparistvl",
  "password": "j&o99?Pm2#Uj",
  "rememberMe": "true"
}
```
Response:
```json
{
    "status": "Ok",
    "data": {
        "access_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjExMzU5MjkzRjZBQzkyODk3QkI4NjhENEQ5MTI2N0ZBQjczRTcyNUIiLCJ0eXAiOiJhdCtqd3QiLCJ4NXQiOiJFVFdTa19hc2tvbDd1R2pVMlJKbi1yYy1jbHMifQ.eyJuYmYiOjE3NTY2MTQ0OTAsImV4cCI6MTc1NzgyNDA5MCwiaXNzIjoiaHR0cDovL2FnZW50LWFwaSIsImF1ZCI6WyJhZ2VudCIsImJvb2tpbmciLCJjcmVkaXRtb25pdG9yaW5nIiwiZWFnbGUiLCJnbG9iYWwiLCJtYXN0ZXIiLCJvcmRlciIsInRyYXZlbGFnZW50Il0sImNsaWVudF9pZCI6InJvLmNsaWVudC4xNGQiLCJzdWIiOiI2YWNhYzJmNC00YzM4LTRlZTgtNWM0NS0wOGRkY2YzY2JlZDUiLCJhdXRoX3RpbWUiOjE3NTY2MTQ0OTAsImlkcCI6ImxvY2FsIiwiaWQiOiJ0ZXN0cGFyaXN0dmwiLCJhaWQiOiIwZTQ4MTRmZi1kYzdkLTQ0NzgtNGQ0ZS0wOGRkY2YzYjk3NTUiLCJpc19zdXBlcl9hZG1pbiI6IlRydWUiLCJpc19hZG1pbiI6IlRydWUiLCJlbWFpbCI6Im11bHlhZGlfcGFyaXNAeWFob28uY29tIiwic2NvcGUiOlsib3BlbmlkIiwiYWdlbnQiLCJib29raW5nIiwiY3JlZGl0bW9uaXRvcmluZyIsImVhZ2xlIiwiZ2xvYmFsIiwibWFzdGVyIiwib3JkZXIiLCJ0cmF2ZWxhZ2VudCJdLCJhbXIiOlsicHdkIl19.LYt9FfZiJqIuutYE_KhXgUWzC3DSbsFeUqwQiHcum9U3UFhYJFybuOTi_JwaX1-pAnNQOLBlLMWpt4F_8aKVL-D3wYULcQrlkQYDjB-370R2_sxYq_Z_MaoQUSklg_V7Ea8nizFJTL6OcZVRHQ0SIAlhYrkzs-N5-vTUClzAN-chniI0Y_QJq-g-g2KOs5wS6rgwRGENDrGh-vEAaoWgetDPlrySYltTSljdQt0qKfr_drZbWyFZKkpDjMV2ioWCKBh9lj21luVWjLPwJIBhaF5UuV5UxS3SJCu9QyMEmXmhCRua6PLyzManT6Iwhhu13MTxpLvt4tuqah5rT3sXuQ",
        "expires_in": 1209600,
        "token_type": "Bearer",
        "scope": "agent booking creditmonitoring eagle global master openid order travelagent"
    }
}
```

### Get Routes

```bash
GET http://localhost:8003/ferries/routes
```

Response:
```json
{
    "routes": [
        {
            "id": "07adda23-56e2-475d-15ac-08d7934ea487",
            "code": "BTC - HFC",
            "name": "Batam Centre Terminal - HarbourFront Centre Terminal",
            "embarkationPort": {
                "id": "00ec55cd-f45b-47af-faad-08d7934cf062",
                "code": "BTC",
                "name": "Batam Center Terminal"
            },
            "destinationPort": {
                "id": "ecc4544a-10de-4b20-faaa-08d7934cf062",
                "code": "HFC",
                "name": "HarbourFront Centre Terminal"
            },
            "sector": {
                "id": "dbea62f3-a27d-4a20-aa68-b3704c42dfab",
                "code": "BTM - SG",
                "name": "Batam - Singapore"
            }
        },
        {
            "id": "70695ec6-b859-4074-15ad-08d7934ea487",
            "code": "SKP - HFC",
            "name": "Sekupang Terminal - HarbourFront Centre Terminal",
            "embarkationPort": {
                "id": "66e453b2-a85e-40a7-faa9-08d7934cf062",
                "code": "SKP",
                "name": "Sekupang"
            },
            "destinationPort": {
                "id": "ecc4544a-10de-4b20-faaa-08d7934cf062",
                "code": "HFC",
                "name": "HarbourFront Centre Terminal"
            },
            "sector": {
                "id": "dbea62f3-a27d-4a20-aa68-b3704c42dfab",
                "code": "BTM - SG",
                "name": "Batam - Singapore"
            }
        }
    ]
}
```

### Get Trips (Schedule Search)
Description: searching available schdules for user to choose
```bash
GET http://localhost:8003/ferries/transactionshttp://localhost:8003/ferries/trips?origin={origin}&destination={destination}&date={date}
```
Example
```bash
GET http://localhost:8003/ferries/transactionshttp://localhost:8003/ferries/trips?origin=HFC&destination=BTC&date=20250830
```
Response:
```json
{
    "trips": [
        {
            "departureTime": "08:25",
            "arrivalTime": "09:35",
            "status": "OPEN",
            "tripID": "RFPE0825",
            "remarks": "",
            "tripSchedID": 21137,
            "usedSeat": 262,
            "gateOpen": "07:40",
            "gateClose": "08:10"
        },
        {
            "departureTime": "15:40",
            "arrivalTime": "16:50",
            "status": "OPEN",
            "tripID": "RFPE1540",
            "remarks": "",
            "tripSchedID": 21138,
            "usedSeat": 265,
            "gateOpen": "12:55",
            "gateClose": "15:25"
        }
    ]
}
```

### Post Booking
```bash
POST http://localhost:8003/ferries/bookings
```
Request Body:
```json
{
  "isRoundTrip": false,
  "isReturnTripOpen": true,
  "departureCoreApiTrip": {
    "date": "2025-09-01",
    "routeID": "07adda23-56e2-475d-15ac-08d7934ea487",
    "id": "398",
    "time": "0825",
    "gateOpen": "0740",
    "gateClose": "0810"
  },
  "returnCoreApiTrip": null
}

```
Response:
```bash
{
    "status": "Ok",
    "data": "a78b4872-4a54-469e-8f98-08dde6d79212"
}
```

### Add Booking Details
```bash
POST http://localhost:8003/ferries/bookings/{booking_id}/details
```
Example:
```bash
POST http://localhost:8003/ferries/bookings/a78b4872-4a54-469e-8f98-08dde6d79212/details
```
Request Body:
```json
{
  "isRoundTrip": false,
  "isReturnTripOpen": true,
  "departureCoreApiTrip": {
    "date": "2025-09-01",
    "routeID": "07adda23-56e2-475d-15ac-08d7934ea487",
    "id": "398",
    "time": "0825",
    "gateOpen": "0740",
    "gateClose": "0810"
  },
  "returnCoreApiTrip": null
}

```
Response:
```bash
{
    "status": "Ok",
    "data": "bbd01c46-6f10-4b1e-f3b3-08dde6d799be"
}
```

### GET Booking Details
```bash
GET http://localhost:8003/ferries/bookings/{booking_id}/details
```
Example:
```bash
GET http://localhost:8003/ferries/bookings/a78b4872-4a54-469e-8f98-08dde6d79212/details
```

Response:
```json

{
    "status": "Ok",
    "data": {
        "totalRecords": 1,
        "records": [
            {
                "id": "8ce09e8a-ee1b-46ee-f3b4-08dde6d799be",
                "identification": {
                    "type": 0,
                    "no": "A321123",
                    "fullName": "ANDI",
                    "gender": 0,
                    "dateOfBirth": "1991-01-01T00:00:00",
                    "placeOfBirth": null,
                    "issueDate": "2020-09-01T00:00:00",
                    "expiryDate": "2027-09-01T00:00:00",
                    "nationality": {
                        "id": "0dbe8cd6-cb51-4e34-ff90-08d7934c8bf2",
                        "code": "ID",
                        "code2": "INA",
                        "name": "INDONESIA",
                        "nationality": "INDONESIAN",
                        "isSingaporeRequireVisa": false,
                        "isIndonesiaRequireVisa": false
                    },
                    "issuanceCountry": {
                        "id": "0dbe8cd6-cb51-4e34-ff90-08d7934c8bf2",
                        "code": "ID",
                        "code2": "INA",
                        "name": "INDONESIA",
                        "nationality": "INDONESIAN",
                        "isSingaporeRequireVisa": false,
                        "isIndonesiaRequireVisa": false
                    }
                },
                "isCancelled": false,
                "bookingType": {
                    "id": "cce8e162-8fdf-4183-c766-08dbb4d0fd32",
                    "code": "BTM1IDATEST",
                    "name": "BATAM - SINGAPORE 1WAY INDONESIAN PASSPORT ADULT TEST TICKET (ALL IN)",
                    "isRoundTrip": false,
                    "isVTL": false,
                    "hasDayGroupRestriction": false,
                    "hasNationalityRestriction": true,
                    "hasPaxTypeRestriction": false,
                    "additionalCriteriaString": null,
                    "departureSector": {
                        "id": "dbea62f3-a27d-4a20-aa68-b3704c42dfab",
                        "code": "BTM - SG",
                        "name": "Batam - Singapore",
                        "nextSector": {
                            "id": "26ac1736-8822-4b90-a50a-eeaf1a190578",
                            "code": "SG - BTM",
                            "name": "Singapore - Batam",
                            "hasGST": false
                        },
                        "hasGST": false
                    },
                    "allowedDayGroup": null,
                    "allowedNationality": {
                        "id": "0dbe8cd6-cb51-4e34-ff90-08d7934c8bf2",
                        "code": "ID",
                        "code2": "INA",
                        "name": "INDONESIA",
                        "nationality": "INDONESIAN",
                        "isSingaporeRequireVisa": false,
                        "isIndonesiaRequireVisa": false
                    },
                    "allowedPaxType": null
                },
                "departureVoucherCode": null,
                "returnVoucherCode": null
            }
        ]
    }
}

```

### Get Countries

```bash
GET http://localhost:8003/ferries/countries
```

Response:
```json
{
    "countries": [
        {
            "id": "bfec3e93-7ea4-4252-906d-cd3a7b3b4a02",
            "code": "AD",
            "code2": "AND",
            "name": "ANDORRA",
            "nationality": "ANDORRA"
        },
        {
            "id": "a14d6e9f-a9a0-4b50-be88-c64c03214756",
            "code": "AE",
            "code2": "ARE",
            "name": "UNITED ARAB EMIRATES",
            "nationality": "UNITED ARAB EMIRATES"
        },
        {
            "id": "4f18cede-f88f-4870-a2b9-06cbaef785ec",
            "code": "AF",
            "code2": "AFG",
            "name": "AFGHANISTAN",
            "nationality": "AFGHANISTAN"
        },
        {
            "id": "8742d507-8b72-4d5f-949e-ef986c776d08",
            "code": "AG",
            "code2": "ATG",
            "name": "ANTIGUA AND BARBUDA",
            "nationality": "ANTIGUA AND BARBUDA"
        }

        
        
    ]
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