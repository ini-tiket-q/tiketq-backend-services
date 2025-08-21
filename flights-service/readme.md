# Flights Service

This microservice handles the flight-related functionalities for the TiketQ OTA platform. It follows the Hexagonal Architecture (Ports and Adapters) pattern for better maintainability and testability.

---

## 🧱 Folder Structure

```
flights-service/
├── app.py                     # Entry point for the service
├── Dockerfile                 # Container config
├── requirements.txt           # Python dependencies
├── .env.example               # Environment variable template
├── domain/
│   ├── models.py              # Domain models for flights and payments
│   ├── services.py            # Business logic layer (ports)
│   └── repository.py          # Data access interfaces (DB or cache)
├── adapters/
│   └── external_api.py        # External flight provider client (adapter)
└── routes/
│    └── flights.py             # Inbound API (FastAPI route handler)
│    └── payments.py           #  Innound API (FastAPI route handler)
```

---

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
MOCK_REMOTE=true
```


## 🧪 Health Check

### Endpoint:
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


---

## ✅ MMBC Payment Endpoints (via Flight-Service)

This service handles communication with MMBC for flight-related operations such as pricing, booking, and issuing tickets. It does **not** use a database. All data comes from MMBC directly.

These endpoints are defined under `routes/payments.py`, using FastAPI with `services.py` for the logic and `external_api.py` for MMBC communication.

---

## ⚙️ Environment & Tooling

- **FastAPI** — for HTTP routing and Swagger documentation
- **uvicorn** — used as the app server
- **uv** — Python package manager to run the app and install dependencies
- **Docker** — container setup (optional)
- **Swagger Docs** — available at `http://localhost:5001/docs`

To run locally with `uv`:

```bash
uv run uvicorn --app-dir flights-service app:app --reload --port 5001
```


## 🚀 Running Locally (Docker)

### 1. Build the container:
```bash
docker build -t flights-service ./flights-service
```

### 2. Run the container:
```bash
docker run -p 5001:8000 --env-file ./flights-service/.env.example flights-service
```

The service will be accessible at:  
`http://localhost:5001/health`

---

## 🔌 Endpoints Overview

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
