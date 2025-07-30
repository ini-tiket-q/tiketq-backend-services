## TiketQ Backend Microservices Monorepo

This repository contains the backend microservices for TiketQ, an OTA (Online Travel Agent) platform providing flight, ferry, hotel bookings, PPOB services, payments, and API gateway functionalities.

### Overall Structure
```bash
/tiketq-backend/
│
├── docker-compose.yml
├── .env
├── README.md
├── RBAC_DOCUMENTATION.md      # RBAC implementation guide
├── API_SPECIFICATIONS.md       # Detailed API specifications
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
│   ├── test_rbac.py             # RBAC test script
│   ├── openapi.json             # OpenAPI specification
│   ├── domain/
│   │    ├── models.py           # Core domain models (User, Token, Role, etc)
│   │    ├── services.py         # Business logic (ports) with RBAC
│   │    └── repository.py       # Repository interfaces (DB port)
│   ├── adapters/
│   │    ├── db.py               # DB implementation (adapter) with role support
│   │    └── api.py              # External API clients if any
│   └── routes/
│        └── auth_routes.py      # REST API adapter (inbound) with RBAC middleware
│
├── user-service/
│   ├── app.py                   # User profile management service
│   ├── Dockerfile               # Container configuration
│   ├── requirements.txt
│   ├── test_user_service.py     # User service test script
│   ├── openapi.json             # OpenAPI specification
│   ├── README.md                # User service documentation
│   ├── domain/
│   │    ├── models.py           # User profile models with role support
│   │    ├── services.py         # Business logic (ports)
│   │    └── repository.py       # User DB interface
│   ├── adapters/
│   │    ├── db.py               # DB adapter for user data with role support
│   │    └── api.py              # External API clients if any
│   └── routes/
│        └── user_routes.py      # REST API adapter (inbound) with RBAC
│
├── transaction-service/
│   ├── app.py                   # Transaction management service
│   ├── Dockerfile               # Container configuration
│   ├── requirements.txt
│   ├── README.md                # Transaction service documentation
│   ├── domain/
│   │    ├── models.py           # Transaction, Order, Payment models
│   │    ├── services.py         # Business logic (ports)
│   │    └── repository.py       # Transaction DB interface
│   ├── adapters/
│   │    ├── db.py               # DB adapter for transaction data
│   │    ├── payment_gateway.py  # Payment gateway integration
│   │    └── webhook_handler.py  # Webhook handlers
│   └── routes/
│        ├── transaction_routes.py # Transaction management API
│        ├── order_routes.py      # Order processing API
│        └── payment_routes.py    # Payment processing API
│
├── flights-service/
│   ├── app.py
│   ├── Dockerfile               # Container configuration
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
│   ├── app.py
│   ├── Dockerfile               # Container configuration
│   ├── requirements.txt
│   ├── domain/
│   │    ├── models.py           # Ferry domain models
│   │    ├── services.py         # Business logic (ports)
│   │    └── repository.py       # Repository interfaces
│   ├── adapters/
│   │    └── external_api.py     # External ferry provider clients
│   └── routes/
│        └── ferries.py          # Inbound API
│
├── hotels-service/
│   ├── app.py
│   ├── Dockerfile               # Container configuration
│   ├── requirements.txt
│   ├── domain/
│   │    ├── models.py           # Hotel domain models
│   │    ├── services.py         # Business logic (ports)
│   │    └── repository.py       # Repository interfaces
│   ├── adapters/
│   │    └── external_api.py     # External hotel provider clients
│   └── routes/
│        └── hotels.py           # Inbound API
│
├── ppob-service/
│   ├── app.py
│   ├── Dockerfile               # Container configuration
│   ├── requirements.txt
│   ├── domain/
│   │    ├── models.py           # PPOB domain models
│   │    ├── services.py         # Business logic (ports)
│   │    └── repository.py       # Repository interfaces
│   ├── adapters/
│   │    └── external_api.py     # External PPOB provider clients
│   └── routes/
│        └── ppob.py             # Inbound API
│
├── payment-service/
│   ├── app.py
│   ├── Dockerfile               # Container configuration
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
├── secrets/                     # Create this please, see Docker-compose for reference
│   └── db_user.txt
│
└── postgres/
    └── init.sql                 # DB schema with user, auth, role, and transaction tables

```

----

### Overview
The backend is implemented as a collection of loosely coupled microservices within a monorepo, each responsible for a specific domain:

- `api-gateway`: Routes incoming client requests to appropriate services.
- `auth-service`: Manages user authentication, authorization, and **Role-Based Access Control (RBAC)**.
- `user-service`: Handles user profile management with **RBAC-protected endpoints**.
- `transaction-service`: Manages booking transactions, order processing, and payment confirmations.
- `flights-service`, `ferries-service`, `hotels-service`, `ppob-service`: Integrate with various external APIs to provide booking and information services.
- `payment-service`: Manages payment processing and related webhooks.
- `postgres`: Contains database schema initialization scripts with role support.

### 🔐 Role-Based Access Control (RBAC)

The system implements a comprehensive RBAC system with two roles:

#### **USER Role**
- Can access their own profile information
- Can update their own profile
- Cannot access other users' data
- Cannot perform administrative functions

#### **ADMIN Role**
- Full access to all user data
- Can create, read, update, and delete any user profile
- Can manage user roles
- Can list all users in the system

#### **RBAC Features**
- **JWT Token Enhancement**: Tokens include role information
- **Role-based Authorization**: Different access levels based on user role
- **Ownership Validation**: Users can only access their own data
- **Database Constraints**: Role values are constrained at database level
- **Middleware Protection**: All protected endpoints use RBAC middleware

#### **Protected Endpoints**

| Service | Endpoint | USER | ADMIN | Description |
|---------|----------|------|-------|-------------|
| Auth | `/auth/register` | ✅ | ✅ | Register new user |
| Auth | `/auth/login` | ✅ | ✅ | Login user |
| Auth | `/auth/me` | ✅ | ✅ | Get own info |
| Auth | `/auth/users` | ❌ | ✅ | List all users |
| Auth | `/auth/users/{id}` | ❌ | ✅ | Get specific user |
| Auth | `/auth/users/{id}/role` | ❌ | ✅ | Update user role |
| User | `POST /users/` | ❌ | ✅ | Create profile |
| User | `GET /users/{id}` | ✅* | ✅ | Get profile |
| User | `PUT /users/{id}` | ✅* | ✅ | Update profile |
| User | `DELETE /users/{id}` | ❌ | ✅ | Delete profile |
| User | `GET /users/` | ❌ | ✅ | List all users |
| Transaction | `POST /transactions/` | ✅ | ✅ | Create transaction |
| Transaction | `GET /transactions/{id}` | ✅* | ✅ | Get transaction |
| Transaction | `POST /transactions/{id}/refund` | ❌ | ✅ | Process refund |

*Users can only access their own profiles/transactions

### 📚 API Documentation

All services provide comprehensive API documentation:

#### **Interactive Documentation**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

#### **Service-Specific Documentation**
- **Auth Service**: Complete authentication and user management APIs
- **User Service**: User profile management with RBAC protection
- **Transaction Service**: Transaction management, order processing, and payment handling
- **OpenAPI Specifications**: Available in each service directory

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
├── Dockerfile                # Container configuration
├── requirements.txt          # Python dependencies
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
- The database (PostgreSQL) stores **user-related data**, **authentication data**, and **ticketing information**.
- **Role-based access control** is enforced at both application and database levels.
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
 | (RBAC)        |        |  Ferries, PPOB,  |
 +---------------+        |  Payments, User) |
         |                +-----------------+
         |                         |
         |                         |
         |           +-------------+--------------+
         |           |                            |
 +---------------+  +----------------+        +----------------+
 |   Database    |  | External APIs  |        | External APIs  |
 | (User, Auth,  |  | (Flight APIs,  |        | (Midtrans, PLN,|
 |  Roles)       |  | Hotels, etc)   |        |  other 3rd party|
 +---------------+  +----------------+        +----------------+
```

### Communication Flow
1. The **API Gateway** serves as the entry point, routing client requests to appropriate microservices.
2. It validates requests by communicating with the **Auth Service** using **RBAC-protected tokens**.
3. Microservices process requests by invoking their domain logic with **role-based authorization**.
4. To fulfil requests, services interact with external APIs via outbound adapters or with the database where applicable.
5. Responses are returned back through the API Gateway to the client.

### Getting Started
- Ensure environment variables are correctly set in .env.
- Run docker-compose up to start all services and dependencies.
- Explore each service's /routes directory to understand available API endpoints.
- Review the /domain folders for business logic implementation.
- Adapters in /adapters demonstrate integration with databases and external APIs.

### Testing RBAC
```bash
# Test auth-service RBAC functionality
cd auth-service
python test_rbac.py

# Test user-service functionality
cd user-service
python test_user_service.py
```

### Example commands to run the stack

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs of a specific service, e.g., auth-service
docker-compose logs -f auth-service

# Run API Gateway locally (if you want to skip Docker)
cd api-gateway
pip install -r requirements.txt
python app.py

# Test RBAC functionality
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "adminpass", "role": "admin"}'

# Access API documentation
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

### Documentation
- **RBAC_DOCUMENTATION.md**: Comprehensive guide to the RBAC implementation
- **user-service/README.md**: Detailed documentation for the user service
- **OpenAPI Specifications**: Available in each service directory
- **Interactive API Docs**: Swagger UI and ReDoc for all services
- Each service contains its own documentation and test scripts