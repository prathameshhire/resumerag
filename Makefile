.PHONY: up down logs test-backend test-frontend test migrate

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test-backend:
	docker compose exec backend pytest

test-frontend:
	docker compose exec frontend npm run test

test: test-backend test-frontend

migrate:
	docker compose exec backend alembic upgrade head
