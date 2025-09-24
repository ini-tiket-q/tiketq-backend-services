# Ferries Service

Ferries Service is one of the microservices in the **TiketQ** project, responsible for handling ferry-related data and operations.  
It is built with **FastAPI** and runs as a standalone container in Docker.



## 🚀 Project Structure
```
.
│   app.py                # Main application entry point
│   Dockerfile            # Docker configuration
│   README.md             # Project documentation
│   requirements.txt      # Python dependencies
│
├───adapters
│       external_api.py   # External ferry API integration
│       ext_api_config.py # API configuration
│       payment_client.py # Payment gateway client
│
├───domain
│       db_models.py      # Database models
│       models.py         # Domain models
│       repository.py     # Database repository layer
│       services.py       # Business logic layer
│
├───routes
│       ferries.py        # API route handlers
│
├───utils
│       date_utils.py     # Date/time utilities
│
└───__pycache__           # Compiled Python cache
```


## 📋 Prerequisites

Before running this service, make sure you have:

- **Python 3.11** (if running without Docker)
- **Docker** & **Docker Compose** (recommended for faster setup)
- `.env` file at the project root containing the required environment variables



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

The service will run at:
👉 http://localhost:8000 -> api gateway and http://localhost:8005 -> for ferries service



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
curl http://localhost:8005/
```
Sample response:

```json
{
    "service": "Ferries Service",
    "status": "running",
    "version": "1.0.0"
}
```

## 🔑 Authentication
All API requests require a Bearer Token in the Authorization header.
Example:
```bash
--header 'Authorization: Bearer testdummy123'
```



## 🔍 Basic Endpoints

This project use real APIs provided by Sindo Ferry to create, display, update, and delete data


### Get Routes

```bash
GET api/v1/ferries/routes' \
--header 'Authorization: Bearer testdummy123'

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

### Get Trips Oneway (Schedule Search)
Description: searching available schdules for user to choose
```bash
GET api/v1/ferries/trips/search/oneway?nationality=ID&origin=HFC&destination=BTC&date=2025-09-24&pax=1&ferry_class=Economy%20Class' \
--header 'Authorization: Bearer testdummy123' \
--data ''
```

Response:
```json
{
    "status": "success",
    "departure_trips": [
        {
            "trip_sched_id": "21237",
            "departure_time": "08:25",
            "arrival_time": "09:35",
            "status": "OPEN",
            "trip_id": "RFPE0825",
            "remarks": "",
            "used_seat": "265",
            "gate_open": "07:40",
            "gate_close": "08:10",
            "nationality": "ID",
            "origin": "HFC",
            "destination": "BTC",
            "depart_date": "2025-09-24",
            "return_date": null,
            "pax": 1,
            "ferry_class": "Economy Class",
            "is_round_trip": false,
            "route_id": "8c813cc8-00bd-4778-15b0-08d7934ea487",
            "route_name": "HarbourFront Centre Terminal - Batam Centre Terminal",
            "route": "HFC-BTC",
            "metadata": {
                "trip_sched_id": "21237",
                "route": "HFC-BTC",
                "departure_time": "08:25"
            }
        },
        {
            "trip_sched_id": "21238",
            "departure_time": "15:40",
            "arrival_time": "16:50",
            "status": "OPEN",
            "trip_id": "RFPE1540",
            "remarks": "",
            "used_seat": "266",
            "gate_open": "12:55",
            "gate_close": "15:25",
            "nationality": "ID",
            "origin": "HFC",
            "destination": "BTC",
            "depart_date": "2025-09-24",
            "return_date": null,
            "pax": 1,
            "ferry_class": "Economy Class",
            "is_round_trip": false,
            "route_id": "8c813cc8-00bd-4778-15b0-08d7934ea487",
            "route_name": "HarbourFront Centre Terminal - Batam Centre Terminal",
            "route": "HFC-BTC",
            "metadata": {
                "trip_sched_id": "21238",
                "route": "HFC-BTC",
                "departure_time": "15:40"
            }
        }
    ],
    "return_trips": null
}
```
### Get Trips Roundtrip (Schedule Search)
Description: searching available schdules for user to choose
```bash
GET api/v1/ferries/trips/search/oneway?origin=BTC&destination=HFC&date=2025-09-24&nationality=ID&pax=1&ferry_class=Economy Class&return_date=2025-09-26' \
--header 'Authorization: Bearer testdummy123' \
--data ''
```

Response:
```json
{
    "status": "success",
    "departure_trips": [
        {
            "trip_sched_id": "21235",
            "departure_time": "12:15",
            "arrival_time": "13:25",
            "status": "OPEN",
            "trip_id": "490",
            "remarks": "",
            "used_seat": "265",
            "gate_open": "11:30",
            "gate_close": "12:00",
            "nationality": "ID",
            "origin": "BTC",
            "destination": "HFC",
            "depart_date": "2025-09-24",
            "return_date": null,
            "pax": 1,
            "ferry_class": "Economy Class",
            "is_round_trip": false,
            "route_id": "07adda23-56e2-475d-15ac-08d7934ea487",
            "route_name": "Batam Centre Terminal - HarbourFront Centre Terminal",
            "route": "BTC-HFC",
            "metadata": {
                "trip_sched_id": "21235",
                "route": "BTC-HFC",
                "departure_time": "12:15"
            }
        },
        {
            "trip_sched_id": "21236",
            "departure_time": "19:00",
            "arrival_time": "20:10",
            "status": "OPEN",
            "trip_id": "394",
            "remarks": "",
            "used_seat": "264",
            "gate_open": "18:00",
            "gate_close": "18:45",
            "nationality": "ID",
            "origin": "BTC",
            "destination": "HFC",
            "depart_date": "2025-09-24",
            "return_date": null,
            "pax": 1,
            "ferry_class": "Economy Class",
            "is_round_trip": false,
            "route_id": "07adda23-56e2-475d-15ac-08d7934ea487",
            "route_name": "Batam Centre Terminal - HarbourFront Centre Terminal",
            "route": "BTC-HFC",
            "metadata": {
                "trip_sched_id": "21236",
                "route": "BTC-HFC",
                "departure_time": "19:00"
            }
        }
    ],
    "return_trips": null
}
```

### Post Booking
```bash
POST api/v1/ferries/bookings
--header 'Authorization: Bearer testdummy123'
```
Request Body:
```json
{
  "isRoundTrip": false,
  "isReturnTripOpen": true,
  "departureCoreApiTrip": {
    "date": "2025-09-24",
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
POST api/v1/ferries/bookings/{booking_id}/details
--header 'Authorization: Bearer testdummy123'
```
Example:
```bash
POST api/v1/ferries/bookings/21322f49-236b-425c-d690-08ddf9cd8722/details
--header 'Authorization: Bearer testdummy123'
```
Request Body:
```json
{
  "identification": {
    "type": 0,
    "no": "A321123",
    "fullName": "Lala",
    "gender": 0,
    "dateOfBirth": "1991-01-01",
    "placeOfBirth": null,
    "issueDate": "2020-09-01",
    "expiryDate": "2027-09-01",
    "nationalityID": "0dbe8cd6-cb51-4e34-ff90-08d7934c8bf2",
    "issuanceCountryID": "0dbe8cd6-cb51-4e34-ff90-08d7934c8bf2"
  },
  "email": "lala@example.com",
  "confirmation_email": "lala@example.com",
  "mobile_phone": "+628123456789",
  "whatsapp_no": "+628123456789"
}


```
Response:
```bash
{
    "status": "Ok",
    "data": "4665341a-d5c9-4680-e013-08ddf9cda522",
    "booking_requirements": {
        "email": "lala@example.com",
        "confirmation_email": "lala@example.com",
        "mobile_phone": "+628123456789",
        "whatsapp_no": "+628123456789"
}

```

### GET Booking Details
```bash
GET api/v1/ferries/bookings/{booking_id}/details
--header 'Authorization: Bearer testdummy123'
```
Example:
```bash
GET api/v1/ferries/bookings/a78b4872-4a54-469e-8f98-08dde6d79212/details
--header 'Authorization: Bearer testdummy123'
```

Response:
```json
{
    "email": "lala@example.com",
    "transaction_type": "BOOKING",
    "currency": "IDR",
    "service_type": "FERRIES",
    "items": [
        {
            "name": "Ferry Ticket 1",
            "price": 355000.0,
            "quantity": 1,
            "description": "Ferry ticket for passenger LALA",
            "metadata": {
                "departure_date": "2025-09-24",
                "ferry_number": "SF-123",
                "operator": "Sindo Ferry",
                "class": "Economy"
            }
        }
    ],
    "subtotal": 355000.0,
    "tax": 35500,
    "discount": 0,
    "total": 390500.0,
    "payment_method": "credit_card",
    "payment_gateway": "MIDTRANS",
    "transaction_metadata": {
        "order_id": "21322f49-236b-425c-d690-08ddf9cd8722",
        "passenger_name": "LALA",
        "booking_reference": "TQ-FR-21322f",
        "ip_address": "192.168.1.100"
    },
    "payment_metadata": {
        "bank_name": "BCA",
        "card_last_digits": "1234",
        "card_type": "visa"
    }
}
```

### Get Countries

```bash
GET api/v1/ferries/countries
--header 'Authorization: Bearer testdummy123'
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

### Get Booking Type Pricing

```bash
GET api/v1/ferries/booking-type-pricings
--header 'Authorization: Bearer testdummy123'
```

Response:
```json
{
    "status": "ok",
    "total": 16,
    "records": [
        {
            "id": "5b3be43a-22ba-4c68-e215-08ddcf3bc41c",
            "code": "BATAM-1WA-SG",
            "name": "1WA BATAM TO SINGAPORE FERRY TICKET (ALL NATIONALITIES)",
            "isRoundTrip": false,
            "departureSector": "Batam - Singapore",
            "price": 440000.0,
            "effectiveDate": "2025-07-29T16:00:00",
            "expiryDate": null
        },
        {
            "id": "fbda69f8-1f4e-4247-e217-08ddcf3bc41c",
            "code": "BATAM-2WA-SG",
            "name": "2WA BATAM FERRY TICKET (ALL NATIONALITIES)",
            "isRoundTrip": true,
            "departureSector": "Batam - Singapore",
            "price": 885000.0,
            "effectiveDate": "2025-07-29T16:00:00",
            "expiryDate": null
        },
        {
            "id": "6be4650c-c01b-4727-e211-08ddcf3bc41c",
            "code": "BTM1IDATEST",
            "name": "BATAM - SINGAPORE 1WAY INDONESIAN PASSPORT ADULT TEST TICKET (ALL IN)",
            "isRoundTrip": false,
            "departureSector": "Batam - Singapore",
            "price": 355000.0,
            "effectiveDate": "2025-07-29T16:00:00",
            "expiryDate": null
        },
        {
            "id": "c92c19a2-915e-4fa1-e213-08ddcf3bc41c",
            "code": "BTM2IDATEST",
            "name": "BATAM 2WAYS INDONESIAN PASSPORT ADULT TEST TICKET (ALL IN)",
            "isRoundTrip": true,
            "departureSector": "Batam - Singapore",
            "price": 710000.0,
            "effectiveDate": "2025-07-29T16:00:00",
            "expiryDate": null
        },
        {
            "id": "b70f2da6-9ee0-4c2c-e216-08ddcf3bc41c",
            "code": "SG-1WA-BATAM",
            "name": "1WA SINGAPORE TO BATAM FERRY TICKET (ALL NATIONALITIES)",
            "isRoundTrip": false,
            "departureSector": "Singapore - Batam",
            "price": 445000.0,
            "effectiveDate": "2025-07-29T16:00:00",
            "expiryDate": null
        },
        {
            "id": "94e8939f-d054-4f63-e21d-08ddcf3bc41c",
            "code": "SG-1WA-TBL",
            "name": "1WA SINGAPORE TO TANJUNG BALAI FERRY TICKET (ALL NATIONALITIES)",
            "isRoundTrip": false,
            "departureSector": "Singapore - Tanjung Balai Karimun",
            "price": 515000.0,
            "effectiveDate": "2025-07-29T16:00:00",
            "expiryDate": null
        },
    ....
    ]
}
```
### Get Available Sectors

```bash
GET api/v1/ferries/sectors
--header 'Authorization: Bearer testdummy123'
```

Response:
```json
{
    "sectors": [
        {
            "id": "a128434c-fe0e-4792-8695-10f4b3ab80eb",
            "code": "TBL - SG",
            "name": "Tanjung Balai Karimun - Singapore",
            "nextSector": {
                "id": "530af832-c759-42e9-84f1-a110b6fb8bfa",
                "code": "SG - TBL",
                "name": "Singapore - Tanjung Balai Karimun",
                "hasGST": false
            },
            "hasGST": false
        },
        {
            "id": "2bd955ed-4a10-4e60-9e34-18844fb5957d",
            "code": "TPI - SG",
            "name": "Tanjung Pinang - Singapore",
            "nextSector": {
                "id": "f69fa122-1198-4984-a4c4-3337349e5fc5",
                "code": "SG - TPI",
                "name": "Singapore - Tanjung Pinang",
                "hasGST": false
            },
            "hasGST": false
        },
        {
            "id": "f69fa122-1198-4984-a4c4-3337349e5fc5",
            "code": "SG - TPI",
            "name": "Singapore - Tanjung Pinang",
            "nextSector": {
                "id": "2bd955ed-4a10-4e60-9e34-18844fb5957d",
                "code": "TPI - SG",
                "name": "Tanjung Pinang - Singapore",
                "hasGST": false
            },
            "hasGST": false
        },
        {
            "id": "530af832-c759-42e9-84f1-a110b6fb8bfa",
            "code": "SG - TBL",
            "name": "Singapore - Tanjung Balai Karimun",
            "nextSector": {
                "id": "a128434c-fe0e-4792-8695-10f4b3ab80eb",
                "code": "TBL - SG",
                "name": "Tanjung Balai Karimun - Singapore",
                "hasGST": false
            },
            "hasGST": false
        },
        {
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
        {
            "id": "26ac1736-8822-4b90-a50a-eeaf1a190578",
            "code": "SG - BTM",
            "name": "Singapore - Batam",
            "nextSector": {
                "id": "dbea62f3-a27d-4a20-aa68-b3704c42dfab",
                "code": "BTM - SG",
                "name": "Batam - Singapore",
                "hasGST": false
            },
            "hasGST": false
        }
    ]
}
```




## 🛠 Troubleshooting
Database connection failed
Make sure the postgres service in docker-compose.yml is running and the Secret Keys in .env is correct.

Port already in use
Change the PORT value in .env or adjust the --port parameter when starting Uvicorn.