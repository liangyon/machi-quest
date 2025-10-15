# Authentication Setup

## Overview
This backend uses JWT-based authentication for secure, stateless user authentication.

## Setup Instructions

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the **project root directory** (where docker-compose.yml is located) and set the `SECRET_KEY`:

```bash
# Generate a secure secret key
openssl rand -hex 32
```

Create `.env` in the project root (NOT in the backend folder):
```
SECRET_KEY=<your-generated-secret-key>
DATABASE_URL=postgresql://postgres:password@postgres:5432/machi_quest
REDIS_URL=redis://redis:6379
```

**Important:** The `.env` file must be in the same directory as `docker-compose.yml`, NOT in the backend folder.

### 3. Run with Docker Compose
```bash
# Make sure you're in the project root directory (where docker-compose.yml is)
docker compose up --build
```

### 4. Run Database Migrations (if needed)
```bash
docker compose exec backend alembic upgrade head
```

## API Endpoints

### Authentication Endpoints

#### POST /auth/register
Register a new user.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "display_name": "John Doe",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

**Response (201):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "John Doe",
  "avatar_url": "https://example.com/avatar.jpg",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### POST /auth/login
Login and receive JWT access token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### User Endpoints

#### GET /users/me
Get current authenticated user's information with pet references.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "John Doe",
  "avatar_url": "https://example.com/avatar.jpg",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z",
  "pets": ["pet-uuid-1", "pet-uuid-2"]
}
```

## Usage Example

### 1. Register a new user
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "display_name": "John Doe"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123"
  }'
```

### 3. Access protected endpoint
```bash
curl -X GET http://localhost:8000/users/me \
  -H "Authorization: Bearer <your_access_token>"
```

## Security Features

- **Password Hashing**: Uses bcrypt for secure password hashing
- **JWT Tokens**: Stateless authentication with configurable expiration (default: 30 minutes)
- **Environment-based Secrets**: SECRET_KEY must be set via environment variables
- **Bearer Token Authentication**: Standard HTTP Authorization header

## Configuration

Edit `backend/app/core/config.py` to customize:
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (default: 30)
- `ALGORITHM`: JWT algorithm (default: HS256)

## Frontend Integration

When making requests from the frontend:

```javascript
// Store token after login
const response = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
const { access_token } = await response.json();
localStorage.setItem('token', access_token);

// Use token for authenticated requests
const token = localStorage.getItem('token');
const userResponse = await fetch('/users/me', {
  headers: { 
    'Authorization': `Bearer ${token}` 
  }
});
```

## Troubleshooting

### "Could not validate credentials"
- Check that the token is being sent in the Authorization header
- Verify the token hasn't expired
- Ensure SECRET_KEY matches between token creation and validation

### "Email already registered"
- User with this email already exists
- Use login endpoint instead, or use a different email

### "Field required [type=missing, input_value={'DATABASE_URL': ...}, input_type=dict]"
- The SECRET_KEY environment variable is missing
- **Solution:** Create a `.env` file in the **project root** (same directory as docker-compose.yml)
- Generate a secret key: `python -c "import secrets; print(secrets.token_hex(32))"`
- Add to `.env`: `SECRET_KEY=<generated-key>`
- Restart: `docker compose down` then `docker compose up --build`

### "email-validator is not installed"
- Missing dependency for email validation
- This should be fixed by the `pydantic[email]` in requirements.txt
- If error persists: `docker compose down` then `docker compose up --build`
