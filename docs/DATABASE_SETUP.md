# Database Models and Schemas - Implementation Guide

This document explains the database models and Pydantic schemas implementation for Machi Quest.

## Structure

The backend follows a clean separation of concerns:

```
backend/
├── app/
│   ├── db/
│   │   ├── __init__.py          # Database exports
│   │   ├── models.py            # SQLAlchemy ORM models
│   │   └── database.py          # Database configuration & session management
│   ├── schemas/
│   │   ├── __init__.py          # Schema exports
│   │   ├── user.py              # User Pydantic schemas
│   │   ├── pet.py               # Pet Pydantic schemas
│   │   ├── integration.py       # Integration Pydantic schemas
│   │   ├── event.py             # Event Pydantic schemas
│   │   └── goal.py              # Goal Pydantic schemas
│   └── main.py                  # FastAPI application
├── alembic/
│   ├── env.py                   # Alembic environment configuration
│   ├── script.py.mako           # Migration template
│   └── versions/                # Migration files (auto-generated)
└── alembic.ini                  # Alembic configuration
```

## Database Models

All SQLAlchemy models are defined in `app/db/models.py`:

- **User**: User accounts with authentication
- **Pet**: Virtual pets with state management
- **Integration**: OAuth integrations (GitHub, Fitbit, etc.)
- **EventRaw**: Raw webhook/API events
- **Event**: Normalized events
- **Goal**: User-defined goals
- **AuditLog**: Activity logging (optional)
- **MetricsCache**: Cached metrics for dashboards

### Key Features

1. **UUID Primary Keys**: All models use UUID for distributed systems compatibility
2. **Timestamps**: Automatic `created_at` and `updated_at` tracking
3. **Relationships**: Proper foreign key relationships with cascade deletes
4. **Indexes**: Optimized indexes for common query patterns
5. **JSONB**: Flexible JSON storage for metadata and state

## Pydantic Schemas

Schemas are organized by domain in the `app/schemas/` directory:

### Schema Types

Each domain has multiple schema types:

- **Base**: Common fields shared across operations
- **Create**: Fields required for creation
- **Update**: Optional fields for updates
- **Response**: Fields returned to clients (includes DB fields like `id`, timestamps)

### Example Usage

```python
from app.schemas import UserCreate, UserResponse, PetCreate, PetResponse
from app.db import get_db, User, Pet
from fastapi import Depends
from sqlalchemy.orm import Session

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),
        display_name=user.display_name
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

## Database Configuration

Database connection is configured via environment variable:

```bash
DATABASE_URL=postgresql://user:password@localhost:5432/machi_quest
```

Default (if not set): `postgresql://postgres:postgres@localhost:5432/machi_quest`

## Alembic Migrations

### Initial Setup

1. Generate initial migration:
```bash
cd backend
alembic revision --autogenerate -m "Initial migration"
```

2. Apply migration:
```bash
alembic upgrade head
```

### Common Commands

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Environment Variables

Create a `.env` file in the backend directory:

```env
DATABASE_URL=postgresql://user:password@host:port/database
SQL_ECHO=false  # Set to 'true' to see SQL queries in logs
```

## Running the Application

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

## Pet State JSON Schema

The `pets.state_json` field follows this structure:

```json
{
  "energy": 45,        # 0-100
  "hunger": 12,        # 0-100
  "level": 2,          # >= 1
  "xp": 124,           # >= 0
  "last_event_id": "uuid",
  "last_update": "timestamp",
  "traits": {
    "color": "green",
    "mood": "happy"
  }
}
```

## Best Practices

1. **Always use schemas**: Never accept/return raw ORM models in API endpoints
2. **Use database sessions properly**: Always use `Depends(get_db)` for session management
3. **Handle transactions**: Use `db.commit()` and handle exceptions appropriately
4. **Migrations**: Never modify existing migrations; create new ones instead
5. **Indexes**: Add indexes for frequently queried fields
6. **Relationships**: Use `back_populates` for bidirectional relationships

## Next Steps

1. Implement API routes in `app/api/`
2. Add authentication middleware
3. Implement business logic in `app/services/`
4. Add tests in `app/tests/`
5. Set up encryption for integration tokens
6. Implement webhook handlers for integrations
