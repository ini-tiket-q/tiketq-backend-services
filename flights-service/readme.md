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

<br>


## API Endpoints

### Health Check
**GET** `/health`  
Returns service status and configuration presence.

### List Flights
**GET** `/api/v1/flight-service/flights`  
Query Parameters:
- `frm` (optional): Origin IATA code
- `to` (optional): Destination IATA code
- `date_` (optional): Departure date in `YYYY-MM-DD`
- `page` (optional, default: 1): Page number
- `per_page` (optional, default: 10): Items per page

### Get Flight by ID
**GET** `/api/v1/flight-service/flights/{flight_id}`

### Create Flight
**POST** `/api/v1/flight-service/flights`  
Body:
```json
{
    "flight_number": "TQ 102",
    "from_airport": "CGK",
    "to_airport": "SIN",
    "departure_time": "2025-08-15T09:30:00",
    "arrival_time": "2025-08-15T12:25:00",
    "aircraft_type": "A320"
}
```

### Update Flight
**PATCH** `/api/v1/flight-service/flights/{flight_id}`  
Partial update of fields.

### Soft Delete Flight
**DELETE** `/api/v1/flight-service/flights/{flight_id}`

<br>

## Building and Running with Docker

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

## Development Process Summary

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

## 📌 API Endpoints

### Health Check
**GET** `/health`  
Returns service health status and key config checks.

### Flights
- **GET** `/api/v1/flight-service/flights`  
  Query flights with optional filters:  
  - `frm`: IATA code of departure airport  
  - `to`: IATA code of arrival airport  
  - `date_`: YYYY-MM-DD format  
  - `page`: Page number (default: 1)  
  - `per_page`: Items per page (default: 10)

- **GET** `/api/v1/flight-service/flights/{flight_id}`  
  Retrieve a specific flight by ID.

- **POST** `/api/v1/flight-service/flights`  
  Create a new flight record.

- **PATCH** `/api/v1/flight-service/flights/{flight_id}`  
  Update fields for an existing flight.

- **DELETE** `/api/v1/flight-service/flights/{flight_id}`  
  Soft delete a flight (marks as deleted).

<br>

## API Documentation

Once the service is running, you can explore and test all endpoints directly from your browser using the FastAPI docs:

- **Swagger UI**: [http://localhost:5001/docs](http://localhost:5001/docs)  
- **ReDoc**: [http://localhost:5001/redoc](http://localhost:5001/redoc)

Both pages allow you to view available endpoints, their parameters, and send test requests without any external tools.

<br>

## 🐳 Build & Run with Docker

1. **Build the image:**
```bash
docker build -t flights-service ./flights-service
```

2. **Find the Docker network name of the Postgres container:**
```bash
docker inspect -f '{{range $k,$v := .NetworkSettings.Networks}}{{println $k}}{{end}}' postgres
```

3. **Run the container on the same network as Postgres:**
```bash
docker run --rm   --network tiketq-backend-services_tiketq-net   --env-file ./flights-service/.env.example   -p 5001:8000   flights-service
```

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