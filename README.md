## TiketQ Backend Microservices Monorepo

This repository contains the backend microservices for TiketQ, an OTA (Online Travel Agent) platform providing flight, ferry, hotel bookings, PPOB services, payments, and API gateway functionalities.

### Overall Structure
```bash
/tiketq-backend/
│
├── docker-compose.yml
├── .env
├── README.md
│
├── nginx/
│   └── nginx.conf
│
├── shared/
│   ├── logger.py                 # Logger adapter for all services
│   ├── config.py                 # Env loader & shared helpers
│   └── requirements.txt
│
├── api-gateway/
│   ├── app.py                   # Entry point (Adapter: inbound)
│   ├── Dockerfile
│   ├── requirements.txt
│   └── utils/
│       └── forwarder.py         # Adapter: forwarding requests to services
│
├── auth-service/
│   ├── app.py                   # Adapter: inbound API
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── domain/
│   │    ├── models.py           # Core domain models (User, Token, etc)
│   │    ├── services.py         # Business logic (ports)
│   │    └── repository.py       # Repository interfaces (DB port)
│   ├── adapters/
│   │    ├── db.py               # DB implementation (adapter)
│   │    └── api.py              # External API clients if any
│   └── routes/
│        └── auth_routes.py      # REST API adapter (inbound)
│
├── user-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── domain/
│   │    ├── models.py
│   │    ├── services.py
│   │    └── repository.py       # User DB interface
│   ├── adapters/
│   │    ├── db.py               # DB adapter for user data
│   └── routes/
│        └── user.py
│
├── flights-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── domain/
│   │    ├── models.py           # Flight domain models
│   │    ├── services.py         # Business logic (ports)
│   │    └── repository.py       # Maybe for caching or user prefs if needed
│   ├── adapters/
│   │    └── external_api.py     # All external flight provider clients here (adapters)
│   └── routes/
│        └── flights.py          # Inbound API
│
├── ferries-service/
│   ├── ... (same pattern)
│
├── hotels-service/
│   ├── ... (same pattern)
│
├── ppob-service/
│   ├── ... (same pattern)
│
├── payment-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── domain/
│   │    ├── models.py
│   │    ├── services.py
│   │    └── repository.py       # For DB interface
│   ├── adapters/
│   │    ├── midtrans_adapter.py # Midtrans API adapter
│   │    └── webhook_handler.py  # Webhook adapter
│   └── routes/
│        └── payment.py
│
└── postgres/
    └── init.sql                 # DB schema, for user and ticker tables only

```

----

### Overview
The backend is implemented as a collection of loosely coupled microservices within a monorepo, each responsible for a specific domain:

- `api-gateway`: Routes incoming client requests to appropriate services.
- `auth-service`: Manages user authentication and authorization.
- `user-service`: Handles user profile and related data.
- `flights-service`, `ferries-service`, `hotels-service`, `ppob-service`: Integrate with various external APIs to provide booking and information services.
- `payment-service`: Manages payment processing and related webhooks.
- `postgres`: Contains database schema initialization scripts.

### Architecture: Ports and Adapters (Hexagonal Architecture)
To ensure maintainability and adaptability, the services are designed following the **Ports and Adapters** architectural pattern, also known as Hexagonal Architecture. This design separates the core business logic from external dependencies, allowing each component to evolve independently.

### Key Concepts
- **Domain Layer** (Core Logic):
  Contains the business rules and domain models. It is agnostic to external systems such as databases, web frameworks, or third-party APIs. This layer defines ports (interfaces) representing required services or repositories.
- **Adapters:**
  Concrete implementations of ports, acting as bridges between the domain and external systems. These include:
  - **Inbound Adapters:** Handle communication from outside systems into the domain (e.g., REST API endpoints).
  - **Outbound Adapters:** Handle communication from the domain out to external systems (e.g., database clients, third-party API wrappers).

- **Benefits:**
  - Isolates business logic from infrastructure concerns.
  - Simplifies testing by allowing mocking of external dependencies.
  - Enables easy replacement or extension of external services without changing domain logic.

### Repository Structure
Each service follows a consistent structure:

```bash
/service-name/
├── app.py                    # Entry point for the service (API server)
├── domain/                   # Business logic and domain models
│   ├── models.py             # Data models representing core entities
│   ├── services.py           # Business use cases and domain services (ports)
│   └── repository.py         # Interfaces defining data access or external service contracts
├── adapters/                 # Implementations of ports (external API clients, database access)
│   ├── db.py                 # Database client or ORM implementations
│   └── external_api.py       # Wrappers around third-party APIs
└── routes/                   # API routes and controllers (inbound adapters)
    └── *.py
```

### Database Usage
- The database (PostgreSQL) stores only **user-related data** and **ticketing information**.
- Only services that require persistent user or ticket data interact with the database via well-defined repository interfaces and adapters.
- External API data is consumed directly by service adapters without persistence, except where caching or state is explicitly needed.

## Architecture Diagram

```bash
            +------------------+
            |    API Gateway    |  <-- Client requests (REST, etc)
            +------------------+
                     |
         +-----------+------------+
         |                        |
 +---------------+        +----------------+
 | Auth Service  |        |  Other Services |
 | (User tokens) |        | (Flights, Hotels,|
 +---------------+        |  Ferries, PPOB,  |
         |                |  Payments, User) |
         |                +-----------------+
         |                         |
         |                         |
         |           +-------------+--------------+
         |           |                            |
 +---------------+  +----------------+        +----------------+
 |   Database    |  | External APIs  |        | External APIs  |
 | (User, Tickets)|  | (Flight APIs,  |        | (Midtrans, PLN,|
 +---------------+  | Hotels, etc)   |        |  other 3rd party|
                    +----------------+        +----------------+
```

### Communication Flow
1. The **API Gateway** serves as the entry point, routing client requests to appropriate microservices.
2. It validates requests by communicating with the **Auth Service**.
3. Microservices process requests by invoking their domain logic.
4. To fulfil requests, services interact with external APIs via outbound adapters or with the database where applicable.
5. Responses are returned back through the API Gateway to the client.

### Getting Started
- Ensure environment variables are correctly set in .env.
- Run docker-compose up to start all services and dependencies.
- Explore each service’s /routes directory to understand available API endpoints.
- Review the /domain folders for business logic implementation.
- Adapters in /adapters demonstrate integration with databases and external APIs.

### Example commands to run the stack

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs of a specific service, e.g., flights-service
docker-compose logs -f flights-service

# Run API Gateway locally (if you want to skip Docker)
cd api-gateway
pip install -r requirements.txt
python app.py

```