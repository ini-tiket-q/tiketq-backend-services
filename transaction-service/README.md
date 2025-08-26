# Transaction Service

The Transaction Service is responsible for managing booking transactions, order processing, and transaction history in the TiketQ platform. It handles the complete lifecycle of transactions from creation to completion.

## Features

- Create and manage booking transactions
- Process payment confirmations
- Track transaction status and history
- Generate transaction reports
- Handle refunds and cancellations
- Integrate with payment and booking services

## Architecture

The service follows the Hexagonal Architecture pattern:

### Domain Layer
- **Models**: Transaction, Order, Payment, Refund entities
- **Services**: Business logic for transaction processing
- **Repository**: Data access interfaces

### Adapters Layer
- **Database**: PostgreSQL implementation for transaction storage
- **External APIs**: Integration with payment gateways and booking services
- **Event Handlers**: Message queue consumers for async processing

### Routes Layer
- **API Endpoints**: RESTful API for transaction management
- **Webhooks**: Payment gateway webhook handlers
- **Event Publishers**: Message queue publishers for notifications

## API Endpoints

### Transaction Management

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/transactions/` | POST | USER/ADMIN | Create new transaction |
| `/transactions/{id}` | GET | USER/ADMIN | Get transaction details |
| `/transactions/{id}` | PUT | USER/ADMIN | Update transaction |
| `/transactions/{id}/cancel` | POST | USER/ADMIN | Cancel transaction |
| `/transactions/{id}/refund` | POST | ADMIN | Process refund |
| `/transactions/` | GET | USER/ADMIN | List transactions |

### Order Processing

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/orders/` | POST | USER/ADMIN | Create new order |
| `/orders/{id}` | GET | USER/ADMIN | Get order details |
| `/orders/{id}/status` | PUT | ADMIN | Update order status |
| `/orders/` | GET | USER/ADMIN | List orders |

### Payment Processing

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/payments/` | POST | USER/ADMIN | Create payment |
| `/payments/{id}` | GET | USER/ADMIN | Get payment details |
| `/payments/{id}/confirm` | POST | ADMIN | Confirm payment |
| `/payments/{id}/refund` | POST | ADMIN | Process payment refund |
| `/webhooks/payment` | POST | Public | Payment gateway webhook |

### Reports and Analytics

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/reports/transactions` | GET | ADMIN | Transaction reports |
| `/reports/revenue` | GET | ADMIN | Revenue analytics |
| `/reports/refunds` | GET | ADMIN | Refund reports |

## Database Schema

### Transactions Table
```sql
CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_number VARCHAR(255) UNIQUE NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'IDR',
    status VARCHAR(50) NOT NULL,
    payment_method VARCHAR(50),
    payment_gateway VARCHAR(50),
    gateway_transaction_id VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Orders Table
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    order_number VARCHAR(255) UNIQUE NOT NULL,
    service_type VARCHAR(50) NOT NULL,
    service_id VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    booking_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Payments Table
```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER REFERENCES transactions(id),
    payment_method VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'IDR',
    status VARCHAR(50) NOT NULL,
    gateway_response JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### Refunds Table
```sql
CREATE TABLE refunds (
    id SERIAL PRIMARY KEY,
    transaction_id INTEGER REFERENCES transactions(id),
    amount DECIMAL(10,2) NOT NULL,
    reason VARCHAR(255),
    status VARCHAR(50) NOT NULL,
    processed_by INTEGER,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

## Transaction Status Flow

### Transaction States
1. **PENDING**: Transaction created, awaiting payment
2. **PROCESSING**: Payment being processed
3. **COMPLETED**: Payment successful, transaction complete
4. **FAILED**: Payment failed
5. **CANCELLED**: Transaction cancelled by user or system
6. **REFUNDED**: Transaction refunded

### Order States
1. **DRAFT**: Order created, not yet confirmed
2. **CONFIRMED**: Order confirmed, awaiting payment
3. **PAID**: Payment received, booking confirmed
4. **CANCELLED**: Order cancelled
5. **COMPLETED**: Service delivered

## Integration Points

### External Services
- **Payment Gateway**: Midtrans, Xendit integration
- **Booking Services**: Flights, Hotels, Ferries, PPOB services
- **User Service**: User authentication and profile data
- **Notification Service**: Email and SMS notifications

### Message Queue Events
- **Transaction Created**: Notify user and update inventory
- **Payment Confirmed**: Update booking status and send confirmation
- **Transaction Failed**: Notify user and release inventory
- **Refund Processed**: Update booking and notify user

## Security Features

### Authentication & Authorization
- JWT token validation for all protected endpoints
- Role-based access control (USER/ADMIN)
- User can only access their own transactions
- Admin can access all transactions

### Data Protection
- Sensitive payment data encrypted
- PCI DSS compliance for payment processing
- Audit logging for all transaction changes
- Secure webhook validation

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TRANSACTION_DB_URL` | Database connection string | Required |
| `JWT_SECRET` | JWT token signing secret | Required |
| `PAYMENT_GATEWAY_URL` | Payment gateway API URL | Required |
| `PAYMENT_GATEWAY_KEY` | Payment gateway API key | Required |
| `REDIS_URL` | Redis connection for caching | Optional |
| `RABBITMQ_URL` | Message queue connection | Optional |

## Monitoring & Logging

### Metrics
- Transaction success/failure rates
- Payment processing times
- Revenue analytics
- Refund rates and reasons

### Logging
- Structured logging for all transactions
- Payment gateway communication logs
- Error tracking and alerting
- Audit trail for compliance

## Testing

### Test Categories
- **Unit Tests**: Business logic and domain services
- **Integration Tests**: Database and external API integration
- **API Tests**: Endpoint functionality and error handling
- **Payment Tests**: Payment gateway integration
- **Security Tests**: Authentication and authorization

### Test Scripts
- `test_transaction_service.py`: API endpoint testing
- `test_payment_integration.py`: Payment gateway testing
- `test_webhooks.py`: Webhook handler testing

## Deployment

### Docker
```bash
# Build image
docker build -t transaction-service .

# Run container
docker run -p 8000:8000 transaction-service
```

### Docker Compose
```yaml
transaction-service:
  build: ./transaction-service
  ports:
    - "8000:8000"
  environment:
    - TRANSACTION_DB_URL=postgresql://user:pass@db:5432/transactions
    - JWT_SECRET=your-secret-key
  depends_on:
    - postgres
    - redis
```

## API Documentation

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### OpenAPI Specification
- Complete API specification in `openapi.json`
- Request/response examples
- Error code documentation
- Authentication requirements

## Future Enhancements

1. **Multi-currency Support**: Support for multiple currencies
2. **Subscription Billing**: Recurring payment processing
3. **Advanced Analytics**: Real-time transaction analytics
4. **Fraud Detection**: AI-powered fraud detection
5. **Mobile SDK**: Mobile payment integration
6. **International Payments**: Support for international payment methods 