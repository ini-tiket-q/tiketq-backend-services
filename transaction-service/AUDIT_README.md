# 📋 Transaction Service Audit Logging

## What is Audit Logging?

The audit logging system automatically records all important activities in the transaction service, including:

- **User Actions**: Who did what and when
- **API Requests**: All incoming requests and responses
- **Security Events**: Failed logins, suspicious activities
- **Business Events**: High-value transactions, compliance alerts
- **System Errors**: Any problems that occur

Think of it as a security camera for your application - it keeps a record of everything that happens.

## Where Are Logs Stored?

### Development Environment
- **File Location**: `/tmp/transaction-audit.log` (inside the Docker container)
- **Format**: JSON (structured data that's easy to read and analyze)

### How to Access Logs

#### View Current Logs
```bash
# See all audit logs
sudo docker exec transaction-service cat /tmp/transaction-audit.log

# See logs with nice formatting (if you have jq installed)
sudo docker exec transaction-service cat /tmp/transaction-audit.log | jq '.'

# Watch logs in real-time
sudo docker exec transaction-service tail -f /tmp/transaction-audit.log
```

#### Check Recent Container Logs
```bash
# See recent application logs
sudo docker-compose logs transaction-service --tail 20

# Follow logs as they happen
sudo docker-compose logs transaction-service -f
```

## What Gets Logged?

### 🔒 Security Events
- Unauthorized access attempts
- Invalid login tokens
- Suspicious request patterns

### 💰 Business Events
- **High-Value Transactions**: Above 5,000,000 IDR
- **Compliance Alerts**: Above 100,000,000 IDR
- Payment method risks (cash, wire transfers)

### 📊 System Events
- API request/response details
- Error conditions
- Performance issues (slow requests)

### 🔐 Data Privacy
- Credit card numbers are masked: `********`
- Email addresses are partially hidden: `jo***@example.com`
- Phone numbers show only last 4 digits: `***1234`

## Sample Log Entry

```json
{
  "timestamp": "2025-08-23T12:33:38.370675+00:00",
  "event_type": "business.high_value_transaction",
  "level": "BUSINESS",
  "service": "transaction-service",
  "message": "High-value transaction processed",
  "details": {
    "transaction_id": 12345,
    "amount": 7500000,
    "currency": "IDR",
    "user_id": 789,
    "compliance_flag": true
  },
  "environment": "development"
}
```

## Configuration

The audit system is configured in `adapters/audit_config.py`:

- **High-Value Threshold**: 5,000,000 IDR (5 million)
- **Compliance Threshold**: 100,000,000 IDR (100 million)  
- **Log Level**: INFO (can be changed to DEBUG for more details)
- **Data Privacy**: Enabled by default (GDPR compliant)

## Troubleshooting

### No Logs Appearing?
1. Check if the service is running: `sudo docker-compose ps transaction-service`
2. Check container logs: `sudo docker-compose logs transaction-service`
3. Verify the log file exists: `sudo docker exec transaction-service ls -la /tmp/`

### Want More Detailed Logs?
Change the log level in `audit_config.py`:
```python
LOG_LEVEL = "DEBUG"  # Instead of "INFO"
```

### Need to Change Log Location?
Update the log file path in `audit_config.py`:
```python
LOG_FILE = "/app/logs/audit.log"  # Custom location
```

## Important Notes

- Audit logs are **append-only** (cannot be modified once written)
- Sensitive data is automatically **masked** for privacy
- Logs are in **JSON format** for easy processing
- System continues working even if audit logging fails
- Logs help with **compliance** and **security monitoring**

---

**For Developers**: The audit system runs automatically when the service starts. No manual setup needed - just deploy and it works!
