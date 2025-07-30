# Role-Based Access Control (RBAC) Implementation

This document describes the RBAC implementation for the TiketQ backend services.

## Overview

The RBAC system implements two roles:
- **USER**: Regular users with limited access
- **ADMIN**: Administrators with full access

## API Documentation

### Interactive API Documentation

Both services provide interactive API documentation:

- **Auth Service**: http://localhost:8000/docs (Swagger UI) or http://localhost:8000/redoc (ReDoc)
- **User Service**: http://localhost:8000/docs (Swagger UI) or http://localhost:8000/redoc (ReDoc)

### OpenAPI Specifications

- **Auth Service**: `auth-service/openapi.json`
- **User Service**: `user-service/openapi.json`

## Architecture

### Auth Service RBAC

The auth-service now includes role-based authentication and authorization:

#### Models
- `UserRole`: Enum defining available roles (USER, ADMIN)
- `UserCreate`: Registration model with optional role (defaults to USER)
- `TokenData`: Token payload containing email and role
- `UserResponse`: User information response model

#### Database Schema
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(10) DEFAULT 'user' CHECK (role IN ('user', 'admin'))
);
```

#### JWT Token Structure
Tokens now include role information:
```json
{
  "sub": "user@example.com",
  "role": "admin",
  "exp": 1234567890
}
```

#### Auth Service Endpoints

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/auth/register` | POST | Public | Register new user (default role: USER) |
| `/auth/login` | POST | Public | Login user |
| `/auth/verify-token` | POST | Public | Verify token validity |
| `/auth/me` | GET | USER/ADMIN | Get current user info |
| `/auth/users` | GET | ADMIN | List all users |
| `/auth/users/{user_id}` | GET | ADMIN | Get specific user |
| `/auth/users/{user_id}/role` | PUT | ADMIN | Update user role |

### User Service RBAC

The user-service implements role-based access control for user profile management:

#### Models
- `UserRole`: Same enum as auth-service
- `UserProfile`: User profile with role field
- `UserProfileCreate`: Creation model with role
- `UserProfileUpdate`: Update model with optional role

#### Database Schema
```sql
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    date_of_birth VARCHAR(10),
    address TEXT,
    role VARCHAR(10) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

#### User Service Endpoints

| Endpoint | Method | Access | Description |
|----------|--------|--------|-------------|
| `/users/` | POST | ADMIN | Create user profile |
| `/users/{user_id}` | GET | USER/ADMIN | Get user profile (users can only access own) |
| `/users/email/{email}` | GET | USER/ADMIN | Get user by email (users can only access own) |
| `/users/{user_id}` | PUT | USER/ADMIN | Update user profile (users can only update own) |
| `/users/{user_id}` | DELETE | ADMIN | Delete user profile |
| `/users/` | GET | ADMIN | List all users |

## Access Control Rules

### Auth Service
1. **Public Endpoints**: Registration and login
2. **User/Admin Endpoints**: `/me` - users can access their own information
3. **Admin Only Endpoints**: User management and role updates

### User Service
1. **Admin Only Endpoints**: 
   - Create user profiles
   - Delete user profiles
   - List all users
2. **User/Admin Endpoints**:
   - Get user profile (users can only access their own)
   - Update user profile (users can only update their own)
   - Get user by email (users can only access their own)

## Middleware Functions

### Auth Service
- `get_current_user()`: Extracts and validates JWT token
- `require_admin()`: Ensures admin role access
- `require_user_or_admin()`: Ensures user or admin role access

### User Service
- `get_current_user()`: Extracts and validates JWT token
- `require_admin()`: Ensures admin role access
- `require_user_or_admin()`: Ensures user or admin role access with ownership checks

## API Examples

### Authentication

#### Register User
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "role": "user"
  }'
```

#### Login User
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

#### Get Current User Info
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer <your_jwt_token>"
```

### User Management

#### Create User Profile (Admin Only)
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

#### Get User Profile
```bash
# Get own profile (user or admin)
curl -X GET "http://localhost:8000/users/1" \
  -H "Authorization: Bearer <your_token>"

# Get any profile (admin only)
curl -X GET "http://localhost:8000/users/2" \
  -H "Authorization: Bearer <admin_token>"
```

#### Update User Profile
```bash
# Update own profile
curl -X PUT "http://localhost:8000/users/1" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Jane",
    "phone_number": "+0987654321"
  }'
```

#### List All Users (Admin Only)
```bash
curl -X GET "http://localhost:8000/users/?skip=0&limit=10" \
  -H "Authorization: Bearer <admin_token>"
```

#### Update User Role (Admin Only)
```bash
curl -X PUT "http://localhost:8000/auth/users/2/role?role=admin" \
  -H "Authorization: Bearer <admin_token>"
```

## OpenAPI Schema Examples

### Auth Service Schemas

#### UserCreate
```json
{
  "email": "user@example.com",
  "password": "password123",
  "role": "user"
}
```

#### Token Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### UserResponse
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user"
}
```

### User Service Schemas

#### UserProfileCreate
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "date_of_birth": "1990-01-01",
  "address": "123 Main St, City, Country",
  "role": "user"
}
```

#### UserProfile
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

#### UserProfileUpdate
```json
{
  "first_name": "Jane",
  "phone_number": "+0987654321",
  "address": "456 New St, City, Country"
}
```

## Security Features

1. **Token-based Authentication**: JWT tokens with role information
2. **Role-based Authorization**: Different access levels based on user role
3. **Ownership Validation**: Users can only access their own data
4. **Input Validation**: Pydantic models ensure data integrity
5. **Database Constraints**: Role values are constrained at database level

## Testing

Use the provided test scripts:
- `auth-service/test_rbac.py`: Tests auth-service RBAC functionality
- `user-service/test_user_service.py`: Tests user-service functionality

## Environment Variables

Required environment variables:
- `JWT_SECRET`: Secret key for JWT token signing
- `JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 60)
- `AUTH_DB_URL`: Database URL for auth-service
- `USER_DB_URL`: Database URL for user-service

## API Documentation Access

### Swagger UI
- Auth Service: http://localhost:8000/docs
- User Service: http://localhost:8000/docs

### ReDoc
- Auth Service: http://localhost:8000/redoc
- User Service: http://localhost:8000/redoc

### OpenAPI JSON
- Auth Service: http://localhost:8000/openapi.json
- User Service: http://localhost:8000/openapi.json

## Future Enhancements

1. **Fine-grained Permissions**: More specific permissions beyond roles
2. **Permission Groups**: Group-based access control
3. **Audit Logging**: Track access attempts and changes
4. **Token Refresh**: Implement refresh token mechanism
5. **Multi-tenant Support**: Support for multiple organizations 

## 📋 **API_SPECIFICATIONS.md Features**

### **Complete Endpoint Documentation**
- ✅ **Authentication Service**: All 7 endpoints with detailed specifications
- ✅ **User Service**: All 6 endpoints with detailed specifications
- ✅ **Request/Response Examples**: Real JSON examples for all endpoints
- ✅ **Error Handling**: Comprehensive error codes and responses
- ✅ **Access Control**: Clear documentation of RBAC requirements

### **Detailed Information for Each Endpoint**

#### **Request Documentation**
- **Endpoint URLs** with HTTP methods
- **Request bodies** with JSON examples
- **Path parameters** with types and descriptions
- **Query parameters** with validation rules
- **Headers** requirements (Authorization, Content-Type)

#### **Response Documentation**
- **Success responses** with complete JSON examples
- **Response parameters** with types and descriptions
- **HTTP status codes** for all scenarios

#### **Error Documentation**
- **Error response format** with consistent structure
- **HTTP status codes** mapping to error types
- **Error codes** with descriptions and examples
- **Common error scenarios** for each endpoint

### **Additional Sections**

#### **Authentication**
- ✅ **JWT Token Format** and structure
- ✅ **Token Claims** documentation
- ✅ **Token Expiration** rules
- ✅ **Authorization Header** format

#### **Error Handling**
- ✅ **Standard Error Response Format**
- ✅ **HTTP Status Codes** reference
- ✅ **Common Error Codes** table
- ✅ **Validation Rules** for all fields

#### **Data Types & Validation**
- ✅ **Common Data Types** reference
- ✅ **Validation Rules** for all fields
- ✅ **Pagination** parameters and examples
- ✅ **Versioning** information

#### **Testing & Tools**
- ✅ **Test Scripts** references
- ✅ **Manual Testing** instructions
- ✅ **Automated Testing** tool suggestions
- ✅ **Interactive Documentation** links

### **Key Features**

1. **Comprehensive Coverage**: Every endpoint documented with examples
2. **RBAC Integration**: Clear access control requirements for each endpoint
3. **Error Scenarios**: All possible error responses documented
4. **Real Examples**: Actual curl commands and JSON responses
5. **Validation Rules**: Complete field validation documentation
6. **Testing Guidance**: Tools and methods for testing APIs

### **Documentation Structure**

```
API_SPECIFICATIONS.md
├── Authentication Service (7 endpoints)
│   ├── Register User
│   ├── Login User
│   ├── Verify Token
│   ├── Get Current User Info
│   ├── List All Users (Admin)
│   ├── Get User by ID (Admin)
│   └── Update User Role (Admin)
├── User Service (6 endpoints)
│   ├── Create User Profile (Admin)
│   ├── Get User Profile by ID
│   ├── Get User Profile by Email
│   ├── Update User Profile
│   ├── Delete User Profile (Admin)
│   └── List All Users (Admin)
├── Error Handling
├── Authentication
├── Rate Limiting
├── Data Types
├── Pagination
├── Versioning
└── Testing
```

This comprehensive API specification document serves as a complete reference for developers integrating with the TiketQ backend services, providing everything needed to understand, test, and implement API integrations. 