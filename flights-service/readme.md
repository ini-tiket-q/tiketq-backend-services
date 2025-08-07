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
│   ├── models.py              # Domain models for flights
│   ├── services.py            # Business logic layer (ports)
│   └── repository.py          # Data access interfaces (DB or cache)
├── adapters/
│   └── external_api.py        # External flight provider client (adapter)
└── routes/
    └── flights.py             # Inbound API (FastAPI route handler)
```

---

## ⚙️ Environment Variables

All env variables are loaded via `python-dotenv`. See `.env.example` for reference.

```env
PORT=5001
ENV=development
DEBUG=true
FLIGHTS_DB_URL=postgresql://postgres:postgres@postgres:5432/tiketq_db
EXTERNAL_FLIGHT_API_KEY=your_flight_api_key_here
```

---

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