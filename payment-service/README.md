# TiketQ Payment Service

This service handles payment processing for the TiketQ platform using Midtrans as the payment gateway. It follows the hexagonal architecture (ports and adapters) pattern to ensure clean separation of concerns and maintainability.

## Architecture Overview

The payment service is structured according to the hexagonal architecture pattern:

### Domain Layer (Core)
- **Models**: Domain entities and value objects
- **Services**: Business logic and use cases
- **Repository Interfaces (Ports)**: Contracts for external dependencies

### Adapters Layer
- **Inbound Adapters**: REST API endpoints that accept requests from clients
- **Outbound Adapters**: 
  - Midtrans adapter for payment gateway integration
  - Database adapter for persistent storage

## Features

- Payment creation with multiple payment methods
- Payment status checking
- Payment cancellation
- Payment refunding
- Webhook handling for payment notifications
- Order-based payment tracking

## Payment Methods Supported

- Credit Card
- Bank Transfer
- E-Wallet (GoPay, etc.)
- QRIS
- Retail (Indomaret, etc.)

## Setup and Configuration

### Prerequisites

- Python 3.11+
- PostgreSQL database
- Midtrans account and API keys

### Environment Variables

Copy the `.env.example` file to `.env` and update the values:

```bash
cp .env.example .env
```

Required environment variables:

```
# Midtrans Configuration
MIDTRANS_SERVER_KEY=your_midtrans_server_key
MIDTRANS_CLIENT_KEY=your_midtrans_client_key
MIDTRANS_PRODUCTION=false  # Set to true for production environment

# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=tiketq_db
DB_USER=postgres
DB_PASSWORD=postgres

# Application Configuration
PORT=8000
```

### Running the Service

#### Using Docker

The service is configured to run with Docker Compose:

```bash
docker-compose up payment-service
```

#### Running Locally

```bash
cd payment-service
pip install -r requirements.txt
python app.py
```

## API Endpoints

### Payment Operations

- `POST /payments/`: Create a new payment
- `GET /payments/{payment_id}`: Get payment details
- `GET /payments/{payment_id}/status`: Check payment status
- `POST /payments/{payment_id}/cancel`: Cancel a payment
- `POST /payments/{payment_id}/refund`: Refund a payment
- `GET /payments/order/{order_id}`: Get all payments for an order

### Webhook

- `POST /payments/webhook`: Handle payment notifications from Midtrans

## API Documentation

API documentation is available at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`

## Hexagonal Architecture Implementation

### Domain Layer

The domain layer contains the core business logic and is independent of external concerns:

- `models.py`: Domain entities like PaymentRequest, PaymentResponse
- `services.py`: Business logic for payment operations
- `repository.py`: Interface definitions for external dependencies

### Adapters

#### Inbound Adapters

- `routes/payment.py`: REST API endpoints that accept client requests

#### Outbound Adapters

- `adapters/midtrans_adapter.py`: Implementation of the PaymentRepository interface for Midtrans
- `adapters/db.py`: Implementation of the PaymentStorageRepository interface for database operations

## Testing

To test the payment service:

```bash
# Run unit tests
pytest

# Test webhook handling
curl -X POST "http://localhost:8000/payments/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "test-transaction-123",
    "order_id": "test-order-123",
    "transaction_status": "settlement",
    "gross_amount": "100000.00",
    "payment_type": "credit_card"
  }'
```

## Midtrans Integration

This service integrates with Midtrans using their official Python client library. The integration supports:

1. **Snap API**: For creating payment pages and tokens
2. **Core API**: For direct payment operations like status checks, cancellations, and refunds
3. **Notification Handling**: For processing webhooks from Midtrans

For more information about Midtrans, visit their [official documentation](https://docs.midtrans.com/).
