DB_URL=postgresql://myuser:mypassword@localhost:5432/mydb
ALEMBIC=uv run --package migrations alembic -c migrations/alembic.ini

.PHONY: up down migrate revision psql

up:
	docker compose up -d

down:
	docker compose down

migrate:
	DATABASE_URL=$(DB_URL) $(ALEMBIC) upgrade head

revision:
	DATABASE_URL=$(DB_URL) $(ALEMBIC) revision --autogenerate -m "$(msg)"

psql:
	docker exec -it testpy-postgres-1 psql -U myuser -d mydb
