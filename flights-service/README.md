# ✈️ Flight-Service (TiketQ Backend)

## ✅ Booking + Transaction Integration (MMBC + Transaction-Service)
This service handles communication with MMBC for flight-related operations such as pricing, booking, and issuing tickets. It now also integrates with the `transaction-service` to register bookings and verify payment status.

✅ Bookings made via `/postbooking-json` will automatically trigger a transaction entry and return an `order_number`  
✅ Issuance and status checks (via `/getissued-json`, `/getstatusbooking-json`) will automatically reconcile payment status using the latest transaction record  
⚠️ This service **does not use a database** — in-memory mapping is used to store `kodebooking → order_number` during the session lifecycle. Redis integration is planned for persistence.

---


## 🧱 Folder Structure

```
flights-service/
├── app.py                           # 🚀 Main FastAPI app entry point — wires routes & health check
├── config.py                        # ⚙️ Loads .env file, controls env config like MOCK_REMOTE
├── Dockerfile                       # 🐳 Docker container build config for the service
├── requirements.txt                 # 📦 Python dependencies list
├── .env.example                     # 🧪 Sample environment variable template

├── domain/                          # 💡 Business logic + domain models (Clean/Hexagonal "Core")
│   ├── models.py                    # SQLAlchemy (or Pydantic) data models (if used)
│   ├── schemas_flights.py          # ✈️ Pydantic schemas for flight-related endpoints
│   ├── schemas_bookings.py         # 🧾 Pydantic schemas for booking-related endpoints
│   ├── repository_flights.py       # 📤 Interface to store/retrieve flight data (e.g., DB/cache)
│   ├── repository_bookings.py      # 🧾 Interface to manage booking data (futureproofing DB)
│   ├── services_flights.py         # 🧠 Flight business logic (domain service layer)
│   ├── services_bookings.py        # 💼 Booking business logic (e.g., transform before save/send)
│   └── mmbc_services.py            # 🌐 MMBC API service for booking & pricing (non-adapter logic)

├── adapters/                        # 🔌 I/O Layer (implements ports from domain layer)
│   ├── external_api_flights.py     # 🌐 Real MMBC API client for flight endpoints
│   ├── external_api_bookings.py    # 📩 Real MMBC API client for booking endpoints
│   ├── fake_mmbc.py                # 🧪 Fake unified MMBC mock adapter (flights + bookings)
│   ├── fake_mmbc_flights.py        # 🧪 Mocked flight MMBC implementation (legacy)
│   ├── mmbc_factory.py             # 🏭 Factory: returns either real or mock MMBC client
│   └── store.py                    # 💾 Shared storage logic (e.g., in-memory cache/store)

├── routes/                          # 🌐 Inbound HTTP interface (FastAPI routers)
│   ├── routes_flights.py           # ✈️ `/api/v1/flights/*` endpoints (search, airports, etc.)
│   └── routes_bookings.py          # 📩 `/api/v1/bookings/*` endpoints (price, book, issue)

```



## ⚙️ Environment Variables

All env variables are loaded via `python-dotenv`. See `.env.example` for reference.

```env.example
# ========== FLIGHTS SERVICE ENV ==========
PORT=5001
ENV=development
DEBUG=true

# ========== DATABASE ==========
FLIGHTS_DB_URL=postgresql://postgres:postgres@postgres:5432/tiketq_db

# ========== EXTERNAL API PLACEHOLDER ==========
EXTERNAL_FLIGHT_API_KEY=your_flight_api_key_here

# ========== PROVIDER (MMBC) ==========
MMBC_BASE_URL=https://sandbox.mmbc.example/api
MMBC_USER_ID=your_user_id_here
MMBC_PASSWORD=your_password_here
MMBC_AGENT_CODE=your_agent_code_here
MMBC_TIMEOUT_SECONDS=15
MOCK_REMOTE=true or false (to connect mmbc)
```
#### 🧠 Optional Redis ENV (Not Yet Active)
If Redis is later enabled for caching:

```env
USE_REDIS=true
REDIS_URL=redis://localhost:6379
```


## ⚙️ Environment & Tooling

- **FastAPI** — for HTTP routing and Swagger documentation
- **uvicorn** — used as the app server
- **uv** — Python package manager to run the app and install dependencies
- **Docker** — container setup (optional)





## 🚀 Running Locally (Docker)

### 1. Build the container:
```bash
docker compose build api-gateway flights-service
```

### 2. Run the container:
```bash
docker compose up api-gateway flights-service
```

<br> <br>

<i><b>If you prefer to test with swagger</i></b>:

### 1. Build the container:
```bash
docker build -t flights-service ./flights-service
```
### 2. Run the container:
```bash
docker run -p 8001:8000 --env-file ./flights-service/.env.example flights-service
```
### 3. Accessing Swagger:
To access swagger, access it via http://localhost:8001/docs

<br><br><br>

# 🔌 Endpoints Overview

## 📬 Postman API Collection

You can test the API endpoints using the following Postman collection:

🔗 [Click here to open in Postman](https://rifqisaleh113-727111.postman.co/workspace/Rifqi-Saleh's-Workspace~470e69f4-ec50-477f-8294-6963e5d01d87/request/47257166-0ad9967c-f8c7-4d98-ab3d-7a7bcf8dac37?action=share&creator=47257166&ctx=documentation&active-environment=47257166-39b94003-3b89-450a-8513-23c5ef963bca)

> Make sure to set the correct environment variables if you're using environment-based configurations.



<br><br>

## 🧪 Health Check Endpoint:
```http
GET /health
```

### Example response:
```json
{
  "status": "ok",
  "port": 5001,
  "db_url_present": true,
  "api_key_present": true
}
```
<br><br>


## 🛫 Flight Service Endpoints

### ✅ `/json/ceksaldo` (POST)
Check user balance.

#### Request (form):
- `username`, `password`

#### Response (Success):
```json
{ "result": "ok", "saldo": "1000000" }
```
#### Response (Fail):
```json
{ "result": "no", "reason": "invalid login" }
```

---

### ✅ `/json/getcodearea-json` (GET)
Get airport code and city.

#### Response:
```json
{
  "codes": [
    { "airport": "CGK", "city": "Jakarta" }
  ]
}
```

---

### ✅ `/json/getcodeflights-json` (GET)
Get airline code and name.

#### Response:
```json
[
  { "flight_code": "JT", "flight_name": "Lion Air", "flight_image": "..." }
]
```

---

### ✅ `/json/getflights-json` (GET)
Search available flights.

#### Query Params:
- `username`, `password`
- `flight_from`, `flight_to`, `date`
- Optional: `airline`, `transit`, `baggage`, `flight_class`, `sort_by`, `page`, `per_page`

#### Response:
```json
[
  {
    "flight_id": "1",
    "flight": "Lion Air",
    "flight_code": "JT-101",
    "flight_price": "900000"
  }
]
```
<br><br><br>
## 🧾 Booking Service Endpoints


### 1. `POST /json/getprice-json`
> Get pricing info for a flight from MMBC.

#### Required Body:
```json
{
  "flight": "JT-792",
  "from": "CGK",
  "to": "SUB",
  "date": "30-05-2018",
  "adult": 1,
  "child": 0,
  "infant": 0
}
```

#### ✅ Success Response:
```json
{
  "result": "ok",
  "flight": "JT-792",
  "publish": 1250000,
  "tax": 150000,
  "totalfare": 1400000,
  "flight_shownta": 1360000,
  "flight_realnta": 1350000,
  "flight_availableseat": 5
}
```

#### ❌ Error:
```json
{
  "detail": "MMBC error: <reason>"
}
```

---

### 2. `POST /json/postbooking-json`
> Post a flight booking to MMBC.

#### Required Body:
```json
{
  "flight": "JT-792",
  "from": "CGK",
  "to": "SUB",
  "date": "30-05-2018",
  "adult": 1,
  "child": 0,
  "infant": 0,
  "email": "user@mail.com",
  "phone": "081234567890",
  "passengername": "Mr John Doe",
  "dateofbirth": "02-09-1990",
  "baggagevolume": "20 Kg"
}
```

#### ✅ Success Response:
```json
{
  "result": "ok",
  "kodebooking": "DEV123",
  "reason": ""
}
```

#### ❌ Error:
```json
{
  "result": "no",
  "reason": "Invalid flight code"
}
```

---

### 3. `POST /json/getissued-json`
> Check if the booking has been issued.

#### Required Body:
```json
{
  "kodebooking": "DEV123"
}
```

#### ✅ Success Response:
```json
{
  "result": "ok",
  "ticket_number": "ABC1234567"
}
```

#### ❌ Error Responses:
- **403 — Payment not completed**:
```json
{
  "result": "no",
  "reason": "Payment not completed"
}
```
- **404 — Booking not found**:
```json
{
  "result": "no",
  "reason": "Booking code not found"
}
```

---

### 4. `POST /json/getstatusbooking-json`
> Get current booking status.

#### Required Body:
```json
{
  "kodebooking": "DEV123"
}
```

#### ✅ Success Response:
```json
{
  "result": "ok",
  "status": "PENDING"
}
```

#### ❌ Error:
```json
{
  "result": "no",
  "reason": "Booking not found"
}
```

---

### 5. `POST /json/resetpassword`
> Reset MMBC agent password.

#### Required Body:
```json
{
  "username": "Paris",
  "email": "paris@mail.com",
  "phone": "081234567890",
  "agencode": "JKT-146751",
  "newpassword": "Secure123"
}
```

#### ✅ Success Response:
```json
{
  "result": "ok",
  "message": "Reset simulated"
}
```

#### ❌ Error:
```json
{
  "detail": "MMBC error: agent not found"
}
```

---
