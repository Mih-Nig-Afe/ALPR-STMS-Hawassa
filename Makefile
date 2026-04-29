COMPOSE := docker compose

.PHONY: env up down build ps logs migrate seed smoke test backup backup-smoke restore lint format first-boot

env:
	cp -n .env.example .env || true

up: env
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f --tail=200

migrate:
	$(COMPOSE) run --rm api alembic upgrade head

seed:
	$(COMPOSE) run --rm api python -m app.bootstrap

smoke:
	./scripts/smoke.sh

test:
	$(COMPOSE) run --rm api pytest tests/unit tests/integration

lint:
	$(COMPOSE) run --rm api ruff check services/api services/worker packages/shared tests

format:
	$(COMPOSE) run --rm api ruff format services/api services/worker packages/shared tests

backup:
	./infra/deploy/scripts/backup-db.sh

backup-smoke:
	./infra/deploy/scripts/backup-restore-smoke.sh

restore:
	./infra/deploy/scripts/restore-db.sh

first-boot:
	./infra/deploy/scripts/first-boot.sh
