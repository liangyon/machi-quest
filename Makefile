# Development environment (hot reload)
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

dev-build:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Production environment
prod:
	docker-compose up

prod-build:
	docker-compose up --build

# Common commands
down:
	docker-compose down

clean:
	docker-compose down -v

logs:
	docker-compose logs -f

logs-frontend:
	docker-compose logs -f frontend

logs-backend:
	docker-compose logs -f backend

restart:
	docker-compose restart

ps:
	docker-compose ps
