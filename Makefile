.PHONY: help dev dev-build prod prod-build down clean logs logs-frontend logs-backend logs-worker restart ps health shell-backend shell-worker test

# Default target
help:
	@echo "Machi Quest - Make Commands"
	@echo "============================"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start development environment with hot reload"
	@echo "  make dev-build    - Build and start development environment"
	@echo "  make dev-down     - Stop development environment"
	@echo ""
	@echo "Production:"
	@echo "  make prod         - Start production environment"
	@echo "  make prod-build   - Build and start production environment"
	@echo "  make prod-down    - Stop production environment"
	@echo ""
	@echo "Common:"
	@echo "  make down         - Stop all services (default compose)"
	@echo "  make clean        - Stop and remove volumes (default compose)"
	@echo "  make clean-all    - Stop and remove all volumes (dev and prod)"
	@echo "  make restart      - Restart all services"
	@echo "  make ps           - Show running containers"
	@echo "  make health       - Check service health status"
	@echo ""
	@echo "Logs:"
	@echo "  make logs         - Follow all logs"
	@echo "  make logs-backend - Follow backend logs"
	@echo "  make logs-frontend- Follow frontend logs"
	@echo "  make logs-worker  - Follow worker logs"
	@echo "  make logs-redis   - Follow redis logs"
	@echo "  make logs-postgres- Follow postgres logs"
	@echo ""
	@echo "Testing & Debugging:"
	@echo "  make test         - Run backend tests"
	@echo "  make shell-backend- Shell into backend container"
	@echo "  make shell-worker - Shell into worker container"
	@echo "  make db-migrate   - Run database migrations"
	@echo "  make db-shell     - Connect to PostgreSQL"

# Development environment (hot reload)
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

dev-build:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

dev-down:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

# Production environment
prod:
	docker-compose -f docker-compose.prod.yml up -d

prod-build:
	docker-compose -f docker-compose.prod.yml up --build -d

prod-down:
	docker-compose -f docker-compose.prod.yml down

# Common commands
down:
	docker-compose down

clean:
	docker-compose down -v

clean-all:
	docker-compose -f docker-compose.yml down -v
	docker-compose -f docker-compose.dev.yml down -v
	docker-compose -f docker-compose.prod.yml down -v

restart:
	docker-compose restart

ps:
	docker-compose ps

# Health checks
health:
	@echo "Checking service health..."
	@echo "\nBackend:"
	@curl -f http://localhost:8000/health || echo "Backend not healthy"
	@echo "\n\nFrontend:"
	@curl -f http://localhost:3000 > /dev/null 2>&1 && echo "Frontend: healthy" || echo "Frontend: not healthy"
	@echo "\nPostgres:"
	@docker-compose exec -T postgres pg_isready -U postgres || echo "Postgres not healthy"
	@echo "\nRedis:"
	@docker-compose exec -T redis redis-cli ping || echo "Redis not healthy"

# Logs
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

logs-worker:
	docker-compose logs -f worker

logs-redis:
	docker-compose logs -f redis

logs-postgres:
	docker-compose logs -f postgres

# Shell access
shell-backend:
	docker-compose exec backend /bin/bash

shell-worker:
	docker-compose exec worker /bin/bash

shell-frontend:
	docker-compose exec frontend /bin/sh

# Database
db-migrate:
	docker-compose exec backend alembic upgrade head

db-rollback:
	docker-compose exec backend alembic downgrade -1

db-shell:
	docker-compose exec postgres psql -U postgres -d machi_quest

db-reset:
	docker-compose down -v
	docker-compose up -d postgres redis
	@echo "Waiting for postgres to be ready..."
	@sleep 5
	docker-compose up -d backend
	@echo "Migrations will run automatically"

# Testing
test:
	docker-compose exec backend pytest

test-coverage:
	docker-compose exec backend pytest --cov=app --cov-report=html

# Build commands
build-backend:
	docker-compose build backend

build-frontend:
	docker-compose build frontend

build-worker:
	docker-compose build worker

build-all:
	docker-compose build
