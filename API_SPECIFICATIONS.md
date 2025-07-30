# API Specifications

This document provides detailed specifications for all TiketQ backend API endpoints, including request/response formats, error handling, and examples.

## Table of Contents

- [Authentication Service](#authentication-service)
- [User Service](#user-service)
- [Error Handling](#error-handling)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)

---

## Authentication Service

Base URL: `http://localhost:8000/auth`

### Authentication Endpoints

#### 1. Register User

**Endpoint:** `POST /auth/register`

**Description:** Register a new user account with email, password, and optional role.

**Access:** Public

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "role": "user"
}
```

**Request Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| email | string (email) | Yes | - | User's email address (must be unique) |
| password | string | Yes | - | User's password (minimum 6 characters) |
| role | string | No | "user" | User's role ("user" or "admin") |

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwicm9sZSI6InVzZXIiLCJleHAiOjE2MzQ1Njc4OTB9.signature",
  "token_type": "bearer"
}
```

**Error Responses:**

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 400 | `USER_ALREADY_EXISTS` | User with this email already exists | `{"detail": "User already exists"}` |
| 422 | `VALIDATION_ERROR` | Invalid request data | `{"detail": [{"loc": ["body", "email"], "msg": "invalid email address", "type": "value_error.email"}]}` |

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "adminpass123",
    "role": "admin"
  }'
```

---

#### 2. Login User

**Endpoint:** `POST /auth/login`

**Description:** Authenticate user with email and password to receive JWT token.

**Access:** Public

**Request Body (form-data):**
```
username=user@example.com&password=password123
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | Yes | User's email address |
| password | string | Yes | User's password |

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwicm9sZSI6InVzZXIiLCJleHAiOjE2MzQ1Njc4OTB9.signature",
  "token_type": "bearer"
}
```

**Error Responses:**

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 401 | `INVALID_CREDENTIALS` | Invalid email or password | `{"detail": "Invalid credentials"}` |
| 422 | `VALIDATION_ERROR` | Invalid request data | `{"detail": [{"loc": ["body", "username"], "msg": "field required", "type": "value_error.missing"}]}` |

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

---

#### 3. Verify Token

**Endpoint:** `POST /auth/verify-token`

**Description:** Verify if a JWT token is valid and not expired.

**Access:** Public

**Request Body:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwicm9sZSI6InVzZXIiLCJleHAiOjE2MzQ1Njc4OTB9.signature"
}
```

**Request Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| token | string | Yes | JWT token to verify |

**Response (200 OK):**
```json
{
  "valid": true
}
```

**Error Responses:**

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 401 | `INVALID_TOKEN` | Token is invalid or expired | `{"detail": "Invalid token"}` |
| 422 | `VALIDATION_ERROR` | Invalid request data | `{"detail": [{"loc": ["body", "token"], "msg": "field required", "type": "value_error.missing"}]}` |

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/auth/verify-token" \
  -H "Content-Type: application/json" \
  -d '{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwicm9sZSI6InVzZXIiLCJleHAiOjE2MzQ1Njc4OTB9.signature"
  }'
```

---

#### 4. Get Current User Info

**Endpoint:** `GET /auth/me`

**Description:** Get information about the currently authenticated user.

**Access:** User/Admin (requires authentication)

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user"
}
```

**Response Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| id | integer | User's unique identifier |
| email | string | User's email address |
| role | string | User's role ("user" or "admin") |

**Error Responses:**

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 401 | `INVALID_CREDENTIALS` | Missing or invalid authorization header | `{"detail": "Invalid authentication credentials"}` |
| 401 | `INVALID_TOKEN` | Token is invalid or expired | `{"detail": "Invalid token"}` |
| 404 | `USER_NOT_FOUND` | User not found in database | `{"detail": "User not found"}` |

**Example Usage:**
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwicm9sZSI6InVzZXIiLCJleHAiOjE2MzQ1Njc4OTB9.signature"
```

---

### User Management Endpoints (Admin Only)

#### 5. List All Users

**Endpoint:** `GET /auth/users`

**Description:** Get a list of all users in the system.

**Access:** Admin only

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "email": "admin@example.com",
    "role": "admin"
  },
  {
    "id": 2,
    "email": "user@example.com",
    "role": "user"
  }
]
```

**Error Responses:**

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 401 | `INVALID_CREDENTIALS` | Missing or invalid authorization header | `{"detail": "Invalid authentication credentials"}` |
| 401 | `INVALID_TOKEN` | Token is invalid or expired | `{"detail": "Invalid token"}` |
| 403 | `ADMIN_ACCESS_REQUIRED` | User does not have admin privileges | `{"detail": "Admin access required"}` |

**Example Usage:**
```bash
curl -X GET "http://localhost:8000/auth/users" \
  -H "Authorization: Bearer <admin_token>"
```

---

#### 6. Get User by ID

**Endpoint:** `GET /auth/users/{user_id}`

**Description:** Get information about a specific user by their ID.

**Access:** Admin only

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | integer | Yes | ID of the user to retrieve |

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
```

**Response (200 OK):**
```json
{
  "id": 2,
  "email": "user@example.com",
  "role": "user"
}
```

**Error Responses:**

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 401 | `INVALID_CREDENTIALS` | Missing or invalid authorization header | `{"detail": "Invalid authentication credentials"}` |
| 401 | `INVALID_TOKEN` | Token is invalid or expired | `{"detail": "Invalid token"}` |
| 403 | `ADMIN_ACCESS_REQUIRED` | User does not have admin privileges | `{"detail": "Admin access required"}` |
| 404 | `USER_NOT_FOUND` | User with specified ID not found | `{"detail": "User not found"}` |

**Example Usage:**
```bash
curl -X GET "http://localhost:8000/auth/users/2" \
  -H "Authorization: Bearer <admin_token>"
```

---

#### 7. Update User Role

**Endpoint:** `PUT /auth/users/{user_id}/role`

**Description:** Update the role of a specific user.

**Access:** Admin only

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | integer | Yes | ID of the user to update |

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| role | string | Yes | New role for the user ("user" or "admin") |

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
```

**Response (200 OK):**
```json
{
  "id": 2,
  "email": "user@example.com",
  "role": "admin"
}
```

**Error Responses:**

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 401 | `INVALID_CREDENTIALS` | Missing or invalid authorization header | `{"detail": "Invalid authentication credentials"}` |
| 401 | `INVALID_TOKEN` | Token is invalid or expired | `{"detail": "Invalid token"}` |
| 403 | `ADMIN_ACCESS_REQUIRED` | User does not have admin privileges | `{"detail": "Admin access required"}` |
| 404 | `USER_NOT_FOUND` | User with specified ID not found | `{"detail": "User not found"}` |
| 422 | `INVALID_ROLE` | Invalid role value provided | `{"detail": "Invalid role value"}` |

**Example Usage:**
```bash
curl -X PUT "http://localhost:8000/auth/users/2/role?role=admin" \
  -H "Authorization: Bearer <admin_token>"
```

---

## User Service

Base URL: `http://localhost:8000/users`

### User Profile Endpoints

#### 1. Create User Profile

**Endpoint:** `POST /users/`

**Description:** Create a new user profile.

**Access:** Admin only

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "date_of_birth": "1990-01-01",
  "address": "123 Main St, City, Country",
  "role": "user"
}
```

**Request Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| email | string (email) | Yes | - | User's email address (must be unique) |
| first_name | string | Yes | - | User's first name |
| last_name | string | Yes | - | User's last name |
| phone_number | string | No | null | User's phone number |
| date_of_birth | string | No | null | User's date of birth (YYYY-MM-DD) |
| address | string | No | null | User's address |
| role | string | No | "user" | User's role ("user" or "admin") |

**Response (201 Created):**
```json
{
  "id": 3,
  "email": "newuser@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "date_of_birth": "1990-01-01",
  "address": "123 Main St, City, Country",
  "role": "user",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 400 | `USER_ALREADY_EXISTS` | User with this email already exists | `{"detail": "User with this email already exists"}` |
| 401 | `INVALID_CREDENTIALS` | Missing or invalid authorization header | `{"detail": "Invalid authentication credentials"}` |
| 401 | `INVALID_TOKEN` | Token is invalid or expired | `{"detail": "Invalid token"}` |
| 403 | `ADMIN_ACCESS_REQUIRED` | User does not have admin privileges | `{"detail": "Admin access required"}` |
| 422 | `VALIDATION_ERROR` | Invalid request data | `{"detail": [{"loc": ["body", "email"], "msg": "invalid email address", "type": "value_error.email"}]}` |

**Example Usage:**
```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Authorization: Bearer <admin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "role": "user"
  }'
```

---

#### 2. Get User Profile by ID

**Endpoint:** `GET /users/{user_id}`

**Description:** Get user profile by ID. Users can only access their own profile, admins can access any profile.

**Access:** User/Admin (users can only access own profile)

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | integer | Yes | ID of the user to retrieve |

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "date_of_birth": "1990-01-01",
  "address": "123 Main St, City, Country",
  "role": "user",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 401 | `INVALID_CREDENTIALS` | Missing or invalid authorization header | `{"detail": "Invalid authentication credentials"}` |
| 401 | `INVALID_TOKEN` | Token is invalid or expired | `{"detail": "Invalid token"}` |
| 403 | `ACCESS_DENIED` | User trying to access another user's profile | `{"detail": "Access denied"}` |
| 404 | `USER_NOT_FOUND` | User with specified ID not found | `{"detail": "User not found"}` |

**Example Usage:**
```bash
curl -X GET "http://localhost:8000/users/1" \
  -H "Authorization: Bearer <jwt_token>"
```

---

#### 3. Get User Profile by Email

**Endpoint:** `GET /users/email/{email}`

**Description:** Get user profile by email address. Users can only access their own profile, admins can access any profile.

**Access:** User/Admin (users can only access own profile)

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string (email) | Yes | Email address of the user to retrieve |

**Headers:**
```
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "date_of_birth": "1990-01-01",
  "address": "123 Main St, City, Country",
  "role": "user",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**Error Responses:**

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 401 | `INVALID_CREDENTIALS` | Missing or invalid authorization header | `{"detail": "Invalid authentication credentials"}` |
| 401 | `INVALID_TOKEN` | Token is invalid or expired | `{"detail": "Invalid token"}` |
| 403 | `ACCESS_DENIED` | User trying to access another user's profile | `{"detail": "Access denied"}` |
| 404 | `USER_NOT_FOUND` | User with specified email not found | `{"detail": "User not found"}` |

**Example Usage:**
```bash
curl -X GET "http://localhost:8000/users/email/user@example.com" \
  -H "Authorization: Bearer <jwt_token>"
```

---

#### 4. Update User Profile

**Endpoint:** `PUT /users/{user_id}`

**Description:** Update user profile information. Users can only update their own profile, admins can update any profile.

**Access:** User/Admin (users can only update own profile)

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | integer | Yes | ID of the user to update |

**Headers:**
```
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "first_name": "Jane",
  "phone_number": "+0987654321",
  "address": "456 New St, City, Country"
}
```

**Request Parameters (all optional):**
| Parameter | Type | Description |
|-----------|------|-------------|
| first_name | string | User's first name |
| last_name | string | User's last name |
| phone_number | string | User's phone number |
| date_of_birth | string | User's date of birth (YYYY-MM-DD) |
| address | string | User's address |
| role | string | User's role ("user" or "admin") |

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "phone_number": "+0987654321",
  "date_of_birth": "1990-01-01",
  "address": "456 New St, City, Country",
  "role": "user",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

**Error Responses:**

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 400 | `INVALID_DATA` | Invalid data provided | `{"detail": "Invalid data"}` |
| 401 | `INVALID_CREDENTIALS` | Missing or invalid authorization header | `{"detail": "Invalid authentication credentials"}` |
| 401 | `INVALID_TOKEN` | Token is invalid or expired | `{"detail": "Invalid token"}` |
| 403 | `ACCESS_DENIED` | User trying to update another user's profile | `{"detail": "Access denied"}` |
| 404 | `USER_NOT_FOUND` | User with specified ID not found | `{"detail": "User not found"}` |
| 422 | `VALIDATION_ERROR` | Invalid request data | `{"detail": [{"loc": ["body", "date_of_birth"], "msg": "invalid date format", "type": "value_error.date"}]}` |

**Example Usage:**
```bash
curl -X PUT "http://localhost:8000/users/1" \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "phone_number": "+0987654321"
  }'
```

---

#### 5. Delete User Profile

**Endpoint:** `DELETE /users/{user_id}`

**Description:** Delete a user profile.

**Access:** Admin only

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | integer | Yes | ID of the user to delete |

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
```

**Response (204 No Content):**
```
(No response body)
```

**Error Responses:**

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 401 | `INVALID_CREDENTIALS` | Missing or invalid authorization header | `{"detail": "Invalid authentication credentials"}` |
| 401 | `INVALID_TOKEN` | Token is invalid or expired | `{"detail": "Invalid token"}` |
| 403 | `ADMIN_ACCESS_REQUIRED` | User does not have admin privileges | `{"detail": "Admin access required"}` |
| 404 | `USER_NOT_FOUND` | User with specified ID not found | `{"detail": "User not found"}` |

**Example Usage:**
```bash
curl -X DELETE "http://localhost:8000/users/3" \
  -H "Authorization: Bearer <admin_token>"
```

---

#### 6. List All Users

**Endpoint:** `GET /users/`

**Description:** Get a list of all user profiles with pagination.

**Access:** Admin only

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| skip | integer | No | 0 | Number of records to skip (for pagination) |
| limit | integer | No | 100 | Maximum number of records to return (max 1000) |

**Headers:**
```
Authorization: Bearer <admin_jwt_token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "phone_number": "+1234567890",
    "date_of_birth": "1985-01-01",
    "address": "123 Admin St, City, Country",
    "role": "admin",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  {
    "id": 2,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+0987654321",
    "date_of_birth": "1990-01-01",
    "address": "456 User St, City, Country",
    "role": "user",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

**Error Responses:**

| Status | Error Code | Description | Example |
|--------|------------|-------------|---------|
| 401 | `INVALID_CREDENTIALS` | Missing or invalid authorization header | `{"detail": "Invalid authentication credentials"}` |
| 401 | `INVALID_TOKEN` | Token is invalid or expired | `{"detail": "Invalid token"}` |
| 403 | `ADMIN_ACCESS_REQUIRED` | User does not have admin privileges | `{"detail": "Admin access required"}` |

**Example Usage:**
```bash
curl -X GET "http://localhost:8000/users/?skip=0&limit=10" \
  -H "Authorization: Bearer <admin_token>"
```

---

## Error Handling

### Standard Error Response Format

All API endpoints return errors in a consistent format:

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

| Status Code | Description | Usage |
|-------------|-------------|-------|
| 200 | OK | Successful GET, PUT, PATCH requests |
| 201 | Created | Successful POST requests |
| 204 | No Content | Successful DELETE requests |
| 400 | Bad Request | Invalid request data or business logic errors |
| 401 | Unauthorized | Missing or invalid authentication credentials |
| 403 | Forbidden | Valid credentials but insufficient permissions |
| 404 | Not Found | Requested resource not found |
| 422 | Unprocessable Entity | Validation errors in request data |
| 500 | Internal Server Error | Server-side errors |

### Common Error Codes

| Error Code | Description | HTTP Status |
|------------|-------------|-------------|
| `INVALID_CREDENTIALS` | Missing or invalid authorization header | 401 |
| `INVALID_TOKEN` | JWT token is invalid or expired | 401 |
| `ADMIN_ACCESS_REQUIRED` | User does not have admin privileges | 403 |
| `ACCESS_DENIED` | User trying to access unauthorized resource | 403 |
| `USER_NOT_FOUND` | User with specified ID/email not found | 404 |
| `USER_ALREADY_EXISTS` | User with email already exists | 400 |
| `INVALID_DATA` | Invalid data provided in request | 400 |
| `VALIDATION_ERROR` | Request data validation failed | 422 |

---

## Authentication

### JWT Token Format

All protected endpoints require a valid JWT token in the Authorization header:

```
Authorization: Bearer <jwt_token>
```

### Token Structure

JWT tokens contain the following claims:

```json
{
  "sub": "user@example.com",
  "role": "user",
  "exp": 1634567890
}
```

### Token Claims

| Claim | Type | Description |
|-------|------|-------------|
| sub | string | User's email address (subject) |
| role | string | User's role ("user" or "admin") |
| exp | integer | Token expiration timestamp |

### Token Expiration

- Default expiration: 60 minutes
- Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` environment variable
- Expired tokens return 401 Unauthorized

---

## Rate Limiting

Currently, no rate limiting is implemented. Future versions may include:

- Rate limiting per IP address
- Rate limiting per user account
- Different limits for different user roles
- Configurable limits via environment variables

---

## Data Types

### Common Data Types

| Type | Description | Example |
|------|-------------|---------|
| integer | 32-bit integer | `123` |
| string | UTF-8 string | `"hello world"` |
| email | Valid email address | `"user@example.com"` |
| date | Date in YYYY-MM-DD format | `"1990-01-01"` |
| datetime | ISO 8601 datetime | `"2024-01-01T00:00:00Z"` |
| boolean | true/false value | `true` |

### Validation Rules

| Field | Validation Rules |
|-------|-----------------|
| email | Must be valid email format, unique in system |
| password | Minimum 6 characters |
| first_name | Required, non-empty string |
| last_name | Required, non-empty string |
| phone_number | Optional, string format |
| date_of_birth | Optional, YYYY-MM-DD format |
| address | Optional, string format |
| role | Must be "user" or "admin" |

---

## Pagination

### Pagination Parameters

| Parameter | Type | Default | Maximum | Description |
|-----------|------|---------|---------|-------------|
| skip | integer | 0 | - | Number of records to skip |
| limit | integer | 100 | 1000 | Maximum number of records to return |

### Pagination Example

```bash
# Get first 10 users
GET /users/?skip=0&limit=10

# Get next 10 users
GET /users/?skip=10&limit=10

# Get all users (up to 1000)
GET /users/?skip=0&limit=1000
```

---

## Versioning

Current API version: `v1.0.0`

- Version information is included in OpenAPI specifications
- Future versions will maintain backward compatibility where possible
- Breaking changes will be communicated in advance
- Version-specific endpoints may be added in the future

---

## Testing

### Test Scripts

- `auth-service/test_rbac.py`: Tests RBAC functionality
- `user-service/test_user_service.py`: Tests user service functionality

### Manual Testing

Use the provided curl examples or access the interactive documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Automated Testing

The OpenAPI specifications can be used with tools like:

- Postman
- Insomnia
- REST Client (VS Code)
- Automated API testing frameworks 