# User Service

The User Service is responsible for managing user profiles in the TiketQ platform. It provides CRUD operations for user profile management.

## Features

- Create user profiles
- Retrieve user profiles by ID or email
- Update user profile information
- Delete user profiles
- List all users with pagination

## API Endpoints

### Create User Profile
```
POST /users/
```
**Request Body:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890",
  "date_of_birth": "1990-01-01",
  "address": "123 Main St, City, Country"
}
```

### Get User by ID
```
GET /users/{user_id}
```

### Get User by Email
```
GET /users/email/{email}
```

### Update User Profile
```
PUT /users/{user_id}
```
**Request Body:**
```json
{
  "first_name": "Jane",
  "phone_number": "+0987654321"
}
```

### Delete User Profile
```
DELETE /users/{user_id}
```

### List All Users
```
GET /users/?skip=0&limit=100
```

## Environment Variables

- `USER_DB_URL`: PostgreSQL connection string for user database

## Database Schema

The service uses a `user_profiles` table with the following structure:

- `id`: Primary key (auto-increment)
- `email`: Unique email address
- `first_name`: User's first name
- `last_name`: User's last name
- `phone_number`: Optional phone number
- `date_of_birth`: Optional date of birth
- `address`: Optional address
- `created_at`: Timestamp when record was created
- `updated_at`: Timestamp when record was last updated

## Running the Service

### Local Development
```bash
cd user-service
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Docker
```bash
docker build -t user-service .
docker run -p 8000:8000 user-service
```

### Testing
```bash
python test_user_service.py
```

## Architecture

The service follows the Hexagonal Architecture pattern:

- **Domain Layer**: Contains business logic, models, and repository interfaces
- **Adapters Layer**: Contains database implementations and external API integrations
- **Routes Layer**: Contains FastAPI route definitions

## Dependencies

- FastAPI: Web framework
- SQLAlchemy: ORM for database operations
- PostgreSQL: Database
- Pydantic: Data validation 