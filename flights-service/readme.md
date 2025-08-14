# Flights Service

This microservice handles the flight-related functionalities for the TiketQ OTA platform. It follows the Hexagonal Architecture (Ports and Adapters) pattern for better maintainability and testability.

<br>

## 🧱 Folder Structure

```
flights-service/
├── app.py                     # Main FastAPI app file — loads env variables, sets up routes, starts the service
├── Dockerfile                 # Instructions for building the service into a Docker image
├── requirements.txt           # List of Python packages needed to run the service
├── .env.example               # Template for environment variables (copy to `.env` and fill in real values)
│
├── domain/                    # Core business logic (pure Python, no frameworks)
│   ├── models.py              # Flight data structure (like a blueprint for flight info)
│   ├── services.py            # Functions that handle the main flight logic (create, get, list, paginate, etc.)
│   └── repository.py          # Interface/contract for how we talk to the database
│
├── adapters/                  # Bridges between domain logic and outside systems
│   ├── external_api.py        # Code to call an external flight API if needed
│   └── persistence.py         # Actual database code (PostgreSQL) that follows the repository interface
│
└── routes/                    # HTTP API endpoints (what frontend calls)
    └── flights.py             # FastAPI routes for flights — handles request params, calls services, returns JSON

```
<br>


## ⚙️ Environment Variables

All env variables are loaded via `python-dotenv`. See `.env.example` for reference.

```env
PORT=5001
ENV=development
DEBUG=true
FLIGHTS_DB_URL=postgresql://postgres:postgres@postgres:5432/tiketq_db
EXTERNAL_FLIGHT_API_KEY=your_flight_api_key_here
```

<br>

## 🚀 Running Locally (Docker)

### 1. Build the Docker image
```bash
docker build -t flights-service ./flights-service
```

### 2. Run the service
```bash
NET=$(docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{printf "%s" $k}}{{end}}' postgres)

docker run --rm   --network "$NET"   --env-file ./flights-service/.env.example   -p 5001:8000   flights-service
```

<br>


## Architecture: User Flow, ERD & Business Rules

### 1. User Flow (Happy Path + Edge Cases)

**Search → Book → Pay → Webhook → Confirm**

1. **Search Flights**  
   `GET /flights/search?frm=CGK&to=SIN&date_=2025-09-01&pax=1&cabin=ECONOMY`  
   - Validates IATA codes, cabin class, date  
   - Returns normalized offers from provider stub

2. **Create Booking**  
   `POST /bookings` with contact info, pax counts, and flight snapshot  
   - Persists booking with `status=INCOMPLETE`  
   - Returns `booking_id`

3. **Create/Reuse Payment (Snap)**  
   `POST /payments/{booking_id}/snap`  
   - One payment per booking (unique constraint)  
   - Returns `{payment_id, snap_token, redirect_url}`

4. **Customer Pays (Provider)**  
   - Redirect to Snap (mocked URL)  
   - Payment provider later triggers webhook

5. **Webhook (Midtrans)**  
   `POST /payments/midtrans/webhook` with `{payment_id, raw}`  
   - Marks payment `PAID` or `FAILED`  
   - If paid, marks booking `CONFIRMED`

6. **View Booking**  
   `GET /bookings/{booking_id}` → shows updated status

**Edge Cases**
- Idempotent payment creation  
- Replayed webhooks are safe  
- Booking stays `INCOMPLETE` on payment failure  

---

### 2. ERD

```mermaid
erDiagram
    FLIGHTS {
      string  id PK
      string  flight_number
      string  from_airport  "IATA(3)"
      string  to_airport    "IATA(3)"
      timestamptz departure_time
      timestamptz arrival_time
      string  aircraft_type
      string  gate  nullable
      string  terminal nullable
      string  status  "SCHEDULED/DELAYED/etc"
      text    notes   nullable
      timestamptz deleted_at nullable
    }

    BOOKINGS {
      string  id PK
      string  user_id nullable
      string  contact_name
      string  contact_phone
      string  contact_email
      string  status  "INCOMPLETE/CONFIRMED"
      string  route_from "IATA(3)"
      string  route_to   "IATA(3)"
      timestamptz departure_time
      timestamptz arrival_time
      string  flight_number
      string  airline
      string  cabin
      int     pax_adult
      int     pax_child
      int     pax_infant
      numeric fare_amount
      string  fare_currency
      string  offer_id
      timestamptz created_at
      timestamptz updated_at
    }

    PAYMENTS {
      string  id PK
      string  booking_id FK,UK
      string  provider
      string  status
      numeric amount
      string  currency
      string  snap_token nullable
      string  redirect_url nullable
      json/text raw_provider_payload nullable
      timestamptz created_at
      timestamptz updated_at
    }

    BOOKINGS ||--o| PAYMENTS : "1 — 0..1"
```

---

### 3. Business Logic

### Search
- Validate input (IATA codes, cabin, pax count, date format)
- Query provider, return normalized offers

### Create Booking
- Require valid contact info & pax counts
- Store full offer snapshot in booking
- Initial status: `INCOMPLETE`

### Payment Creation
- Only if booking exists
- Enforce one payment per booking
- Return existing payment if already pending/paid

### Webhook Handling
- Parse `transaction_status` from provider payload
- `capture/settlement` → Payment = `PAID`, Booking = `CONFIRMED`
- `deny/cancel/expire` → Payment = `FAILED`, Booking unchanged
- Idempotent updates

### Booking Retrieval
- Always returns latest booking state

---

### 4. API Documentation

Once the service is running, you can explore and test all endpoints directly from your browser using the FastAPI docs:

- **Swagger UI**: [http://localhost:5001/docs](http://localhost:5001/docs)  
- **ReDoc**: [http://localhost:5001/redoc](http://localhost:5001/redoc)

Both pages allow you to view available endpoints, their parameters, and send test requests without any external tools.

## 5. API Map

| Action                      | Method | Endpoint                                          |
|-----------------------------|--------|---------------------------------------------------|
| Search flights              | GET    | `/flights/search`                                 |
| Create booking              | POST   | `/bookings`                                       |
| Get booking                 | GET    | `/bookings/{booking_id}`                          |
| Create/Reuse payment (Snap) | POST   | `/payments/{booking_id}/snap`                     |
| Webhook (Midtrans)          | POST   | `/payments/midtrans/webhook`                      |
| List flights (Admin)        | GET    | `/flights`                                        |
| Get flight by ID (Admin)    | GET    | `/flights/{id}`                                   |
| Create flight (Admin)       | POST   | `/flights`                                        |
| Patch flight (Admin)        | PATCH  | `/flights/{id}`                                   |
| Soft delete flight (Admin)  | DELETE | `/flights/{id}`                                   |

## 6. API Contract

Below is the explicit API contract for core endpoints.

### POST `/bookings`
**Request**
```json
{
  "contact_name": "Jane Doe",
  "contact_email": "jane@mail.com",
  "contact_phone": "+62812...",
  "pax_adult": 1,
  "pax_child": 0,
  "pax_infant": 0,
  "offer": {
    "offer_id": "xt-7680-2025-09-01-0645",
    "route_from": "CGK",
    "route_to": "SUB",
    "departure_time": "2025-09-01T06:45:00Z",
    "arrival_time": "2025-09-01T08:20:00Z",
    "airline": "AirAsia",
    "flight_number": "XT7680",
    "cabin": "ECONOMY",
    "fare_amount": 537500,
    "fare_currency": "IDR"
  }
}
```

**Responses**
- `201 Created`
```json
{ "booking_id": "cdd6d7bd3a92443dab469b0669", "status": "INCOMPLETE" }
```
- `400 Bad Request` (validation)
```json
{ "error": "VALIDATION_ERROR", "details": {"contact_email": "invalid"} }
```
- `409 Conflict` (duplicate booking for same offer + contact)
- `500 Internal Server Error`



### POST `/payments/{booking_id}/snap`
**Behavior**
- One payment per booking (idempotent). If PENDING/PAID exists, return it.

**Responses**
- `201 Created`
```json
{
  "payment_id": "pay_123",
  "snap_token": "abc",
  "redirect_url": "https://app.midtrans.com/snap/v2/abc"
}
```
- `404 Not Found` (booking)
- `409 Conflict` (already PAID)



### POST `/payments/midtrans/webhook`
**Behavior**
- Verify signature (gateway in later sprint); update `payments.status`.
- On `capture/settlement`: set `PAID`, then set `bookings.status=CONFIRMED`.
- Idempotent on repeat notifications.

**Responses**
- `200 OK` (always; side-effects idempotent)



## 6. Error Envelope & Status Code Policy

**Error Envelope**
```json
{ "error": "CODE", "message": "human readable", "details": { "field": "reason" } }
```
**Codes**: `VALIDATION_ERROR`, `NOT_FOUND`, `CONFLICT`, `UNAUTHORIZED`, `INTERNAL_ERROR`.

**Status Codes**
- 200/201 success
- 400 validation
- 401/403 reserved for gateway-enforced auth (future)
- 404 resource not found
- 409 conflict (duplicates/idempotency)
- 500 unexpected

---

## 7. Sequence Diagram

```mermaid
sequenceDiagram
  participant C as Client
  participant F as Flights Service
  participant M as Midtrans (Snap)
  participant DB as Database

  C->>F: POST /bookings (offer snapshot, contact)
  F->>DB: insert booking(status=INCOMPLETE)
  F-->>C: 201 {booking_id}

  C->>F: POST /payments/{booking_id}/snap
  F->>DB: upsert payment (PENDING)
  F->>M: create Snap transaction
  F-->>C: 201 {payment_id, redirect_url}

  M-->>C: User pays in Snap UI

  M->>F: POST /payments/midtrans/webhook (settlement)
  F->>DB: set payment=PAID; set booking=CONFIRMED
  F-->>M: 200 OK (idempotent)

  C->>F: GET /bookings/{booking_id}
  F-->>C: 200 {status=CONFIRMED}
```


<br>

# Development Process Summary

1. **Environment Setup**
   - Created `.env.example` with `FLIGHTS_DB_URL`, `PORT`, etc.
   - Ensured connection to existing `tiketq_db` via Docker network.

2. **Database Integration**
   - Implemented `SqlAlchemyFlightRepo` with pagination and soft delete.
   - Added unique constraint for `(flight_number, departure_time)`.

3. **Endpoints Implementation**
   - CRUD endpoints for flights.
   - Pagination support with query parameters.
   - Added validation for IATA codes and arrival/departure times.

4. **Testing with curl**
   - Verified create, list, get by ID, update, and delete endpoints.
   - Confirmed soft delete excludes items from list.

5. **Seeding Data**
   - Added `seed_flights.py` for inserting sample flights.

6. **Dockerization**
   - Created `Dockerfile` and `requirements.txt`.
   - Built and ran service connected to Postgres container.

<br>



## 🛠 Steps We Did in Development

1. **Set up FastAPI project** with Hexagonal Architecture (domain, adapters, routes).
2. **Configured SQLAlchemy** with Postgres connection using env vars from `.env.example`.
3. **Added CRUD endpoints** for flights, including:
   - Create
   - Read (list, get by ID)
   - Update (partial)
   - Delete (soft delete)
4. **Implemented pagination & filtering** on the GET `/flights` endpoint.
5. **Tested with cURL** commands to verify:
   - Health check works.
   - Flight creation, listing, retrieval, update, and deletion.
6. **Connected service to Dockerized Postgres** using shared Docker network.
7. **Created seed script** to populate test flight data.
8. **Verified full flow in logs** (create → get → update → delete → get → list).
9. **Documented endpoints & Docker usage** in this README.