# Payment Service

TiketQ Payment Service menggunakan Clean Architecture dengan Midtrans sebagai payment gateway.

## Struktur Proyek

```
payment-service/
├── app.py                      # FastAPI application entry point
├── Dockerfile                  # Container configuration
├── requirements.txt            # Python dependencies
├── domain/                     # Business logic layer
│   ├── models.py              # Domain models & enums
│   ├── services.py            # Business logic services
│   └── repository.py          # Repository interfaces (ports)
├── adapters/                  # External integrations layer
│   ├── midtrans_adapter.py    # Midtrans API adapter
│   ├── db.py                  # Database adapter
│   └── webhook_handler.py     # Webhook processing adapter
└── routes/                    # API endpoints layer
    └── payment.py             # Payment REST API routes
```

## Fitur

### Payment Operations
- ✅ Create payment dengan Midtrans
- ✅ Check payment status
- ✅ Cancel payment
- ✅ Refund payment
- ✅ Get payments by order ID

### Payment Methods Support
- Credit Card
- Bank Transfer (BCA, Mandiri, BNI, BRI)
- E-Wallet (GoPay, OVO, DANA)
- QRIS
- Retail (Indomaret, Alfamart)

### Webhook Integration
- ✅ Signature verification
- ✅ Status mapping
- ✅ Real-time payment updates

## Environment Variables

```bash
# Midtrans Configuration
MIDTRANS_SERVER_KEY=SB-Mid-server-YOUR_SERVER_KEY
MIDTRANS_CLIENT_KEY=SB-Mid-client-YOUR_CLIENT_KEY
MIDTRANS_IS_PRODUCTION=false

# Database Configuration
DATABASE_URL=postgresql://user:password@postgres:5432/tiketq_db

# Service Configuration
PORT=8000
```

## API Endpoints

### Payment Management

#### Create Payment
```http
POST /payments/
Content-Type: application/json

{
  "order_id": "ORDER-12345",
  "amount": 100000.0,
  "payment_method": "credit_card",
  "customer_details": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+6281234567890"
  },
  "item_details": [
    {
      "id": "item1",
      "price": 100000,
      "quantity": 1,
      "name": "Flight Ticket Jakarta-Bali"
    }
  ],
  "description": "Flight booking payment"
}
```

#### Get Payment Details
```http
GET /payments/{payment_id}
```

#### Check Payment Status
```http
GET /payments/{payment_id}/status
```

#### Cancel Payment
```http
POST /payments/{payment_id}/cancel
Content-Type: application/json

{
  "reason": "Customer requested cancellation"
}
```

#### Refund Payment
```http
POST /payments/{payment_id}/refund
Content-Type: application/json

{
  "amount": 50000.0,
  "reason": "Partial refund requested"
}
```

#### Get Payments by Order
```http
GET /payments/order/{order_id}
```

### Webhook
```http
POST /payments/webhook
Content-Type: application/json

{
  "transaction_id": "...",
  "order_id": "...",
  "transaction_status": "settlement",
  "gross_amount": "100000.00",
  "payment_type": "credit_card",
  "signature_key": "..."
}
```

## Running with Docker Compose

Payment service dijalankan sebagai bagian dari microservices architecture:

```bash
# Build and start all services
docker-compose up -d --build

# View payment service logs
docker-compose logs -f payment-service

# Access payment service documentation
# http://localhost:8003/docs
```

## Payment Status Flow

```
PENDING → PROCESSING → SUCCESS
                   ↘
                    FAILED
                   ↗
PENDING → EXPIRED
       ↘
        CANCELED
       ↗
SUCCESS → REFUNDED
```

## Development

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run service locally
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Testing Payment Integration

#### Test Credit Card (Sandbox)
```
Card Number: 4811 1111 1111 1114
CVV: 123
Exp Month: 01
Exp Year: 2025
```

#### Test Bank Transfer
- BCA Virtual Account akan generate nomor VA otomatis
- Simulasi pembayaran melalui Midtrans simulator

## Security Features

- ✅ Webhook signature verification
- ✅ HTTPS enforcement in production
- ✅ Input validation & sanitization
- ✅ API key protection
- ✅ CORS configuration

## Monitoring & Logging

- Structured logging untuk semua payment operations
- Error tracking untuk failed transactions
- Payment status tracking
- Webhook processing logs

## Integration dengan Services Lain

### Transaction Service
```python
# Setelah payment success, notify transaction service
POST /transactions/payments/notify
{
  "order_id": "ORDER-123",
  "payment_id": "payment-123",
  "status": "success",
  "amount": 100000.0
}
```

### User Service
```python
# Update user payment history
POST /users/{user_id}/payments
{
  "payment_id": "payment-123",
  "amount": 100000.0,
  "status": "success"
}
```
