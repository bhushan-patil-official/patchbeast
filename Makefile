SHELL := /bin/bash
DEV  := docker compose -f docker-compose.yml -f docker-compose.dev.yml
PROD := docker compose -f docker-compose.yml -f docker-compose.prod.yml

.PHONY: help env dev dev-d down test test-api test-web lint fmt migrate makemigrations seed seed-demo \
        schema schema-check shell logs prod-up prod-down prod-pull backup restore createsuperuser killswitch-on killswitch-off e2e

help: ## list targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  %-18s %s\n",$$1,$$2}'

env:
	@test -f .env || cp .env.example .env

dev: env ## build + run everything with hot reload (http://localhost:3000, api :8000, mail :8025)
	$(DEV) up --build

dev-d: env ## same as dev, detached
	$(DEV) up --build -d

down: ## stop dev stack
	$(DEV) down

migrate: ## apply DB migrations
	$(DEV) run --rm api python manage.py migrate --noinput

makemigrations: ## create migrations
	$(DEV) run --rm api python manage.py makemigrations

seed: ## seed the (placeholder) launch anchor game + source list
	$(DEV) run --rm api python manage.py seed

seed-demo: ## seed clearly-labelled DEMO content (noindex) for UI work / e2e
	$(DEV) run --rm api python manage.py seed --demo

createsuperuser: ## create admin user
	$(DEV) run --rm api python manage.py createsuperuser

test: test-api test-web ## run all tests inside containers

test-api:
	$(DEV) run --rm -e DJANGO_SETTINGS_MODULE=patchbeast.settings.test api pytest

test-web:
	$(DEV) run --rm --no-deps web sh -c "npm run typecheck && npm run test --if-present"

e2e: ## Playwright smoke tests against the running dev stack (run `make dev-d seed-demo` first)
	cd apps/web && npx playwright test

lint: ## ruff + black + mypy + eslint + prettier + tsc
	$(DEV) run --rm --no-deps api sh -c "ruff check . && black --check . && mypy ."
	$(DEV) run --rm --no-deps web sh -c "npm run lint && npm run typecheck"

fmt:
	$(DEV) run --rm --no-deps api sh -c "ruff check --fix . && black ."

schema: ## regenerate OpenAPI schema + typed client
	$(DEV) run --rm api python manage.py spectacular --format openapi-json --file /repo/packages/api-client/openapi.json --validate
	cd packages/api-client && npm run generate

schema-check: ## fail if committed schema drifted (CI)
	$(MAKE) schema && git diff --exit-code packages/api-client

shell:
	$(DEV) run --rm api python manage.py shell

killswitch-on: ## pause the whole ingest/LLM/publish pipeline
	$(PROD) exec api python manage.py killswitch on

killswitch-off:
	$(PROD) exec api python manage.py killswitch off

logs: ## tail logs (S=service to filter)
	$(DEV) logs -f --tail=100 $(S)

prod-up: ## build + (re)start production stack, migrate
	$(PROD) up -d --build --remove-orphans

prod-down:
	$(PROD) down

backup: ## run a pg_dump now (prod stack) into ./backups
	$(PROD) exec backup /scripts/backup.sh

restore: ## restore: make restore FILE=backups/patchbeast-YYYYmmdd.sql.gz
	@test -n "$(FILE)" || (echo "usage: make restore FILE=backups/<file>.sql.gz" && exit 1)
	./infra/scripts/restore.sh $(FILE)
