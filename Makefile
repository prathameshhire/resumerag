.PHONY: up down logs test-backend migrate

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

test-backend:
	cd backend && pytest

migrate:
	docker compose exec backend alembic upgrade head
