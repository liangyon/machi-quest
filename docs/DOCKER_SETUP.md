# Docker Setup for Machi Quest Backend

The backend is fully configured to work with Docker Compose and will automatically handle database migrations on startup.

## How It Works

The setup includes:

1. **Docker Compose Configuration** (`docker-compose.yml`)
   - PostgreSQL database on port 5432
   - Redis on port 6379
   - Backend API on port 8000
   - Worker service
   - Frontend on port 3000

2. **Automatic Database Migrations**
   - The `docker-entrypoint.sh` script runs on container startup
   - Waits for PostgreSQL to be ready
   - Automatically runs `alembic upgrade head` to apply all migrations
   - Then starts the FastAPI application

3. **Environment Variables**
   - `DATABASE_URL` is set in docker-compose.yml: `postgresql://postgres:password@postgres:5432/machi_quest`
   - This is automatically used by both the application and Alembic migrations

## Quick Start

### 1. Build and Start All Services

```bash
docker-compose up --build
```

This will:
- Build all containers
- Start PostgreSQL and Redis
- Wait for database to be ready
- Run database migrations automatically
- Start the backend API
- Start frontend and worker services

### 2. Access the Application

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Frontend**: http://localhost:3000

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# See migration logs
docker-compose logs backend | grep migration
```

## Database Migrations

### Automatic Migrations (Recommended in Docker)

Migrations run automatically when the backend container starts. You'll see output like:

```
backend_1    | Waiting for postgres...
backend_1    | PostgreSQL started
backend_1    | Running database migrations...
backend_1    | INFO  [alembic.runtime.migration] Running upgrade  -> abc123, Initial migration
backend_1    | Starting application...
```

### Manual Migrations (Development)

If you need to create or run migrations manually:

```bash
# Generate a new migration
docker-compose exec backend alembic revision --autogenerate -m "Add new field"

# Run migrations
docker-compose exec backend alembic upgrade head

# Rollback one migration
docker-compose exec backend alembic downgrade -1

# View migration history
docker-compose exec backend alembic history
```

## Development Workflow

### Make Changes to Models

1. Edit `backend/app/db/models.py`
2. Generate migration:
   ```bash
   docker-compose exec backend alembic revision --autogenerate -m "Your change description"
   ```
3. Review the generated migration in `backend/alembic/versions/`
4. Restart backend to apply:
   ```bash
   docker-compose restart backend
   ```

### Database Access

Connect to the PostgreSQL database:

```bash
# Using docker-compose
docker-compose exec postgres psql -U postgres -d machi_quest

# Or from your host (if psql is installed)
psql -h localhost -p 5432 -U postgres -d machi_quest
# Password: password
```

### Reset Database

```bash
# Stop all services
docker-compose down

# Remove volumes (this deletes all data!)
docker-compose down -v

# Start fresh
docker-compose up --build
```

## Production Deployment

For production, you should:

1. **Use environment variables** from a `.env` file:
   ```bash
   DATABASE_URL=postgresql://user:password@host:5432/dbname
   REDIS_URL=redis://redis:6379
   ```

2. **Remove --reload flag** in production:
   Update `docker-entrypoint.sh`:
   ```bash
   exec uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

3. **Use production-grade PostgreSQL**:
   - External managed database (AWS RDS, Google Cloud SQL, etc.)
   - Or properly configured PostgreSQL with backups

4. **Enable SSL/TLS** for database connections

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Check if postgres is running
docker-compose ps
```

### Database Connection Errors

Verify the DATABASE_URL matches your docker-compose.yml:
```bash
docker-compose exec backend env | grep DATABASE_URL
```

### Migration Errors

```bash
# Check migration status
docker-compose exec backend alembic current

# View migration history
docker-compose exec backend alembic history

# Force upgrade to head
docker-compose exec backend alembic upgrade head
```

### Port Already in Use

If you see "port is already allocated":
```bash
# Stop any existing containers
docker-compose down

# Check what's using the port
# Windows:
netstat -ano | findstr :8000
# Linux/Mac:
lsof -i :8000
```

## File Structure

```
backend/
├── Dockerfile                 # Container build instructions
├── docker-entrypoint.sh       # Startup script (migrations + server)
├── alembic.ini               # Alembic configuration
├── alembic/
│   ├── env.py                # Alembic environment
│   └── versions/             # Migration files
├── app/
│   ├── main.py              # FastAPI application
│   ├── db/
│   │   ├── models.py        # SQLAlchemy models
│   │   └── database.py      # Database config
│   └── schemas/             # Pydantic schemas
└── requirements.txt          # Python dependencies
```

## Next Steps

1. The database schema is now set up and ready
2. Create API routes in `backend/app/api/`
3. Implement business logic in `backend/app/services/`
4. Add tests in `backend/app/tests/`

See `DATABASE_SETUP.md` for more details on the models and schemas.
