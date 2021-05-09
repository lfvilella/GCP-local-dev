-include .env
ENV_FILE_TEMPLATE = "$(PWD)/env-template.env"
ENV_FILE = "$(PWD)/.env"


all:
	@echo "Hello $(LOGNAME), nothing to do by default"
	@echo "Try 'make help'"

help: ## This help.
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all services
	@[ -f $(ENV_FILE) ] || cat $(ENV_PROD_TEMPLATE) $(ENV_FILE_TEMPLATE) > $(ENV_FILE)
	@sleep 2
	@docker-compose up --build -d

restart: ## Restart all services
	@docker-compose restart

cmd: start ## Access backend bash
	@docker-compose exec backend /bin/bash

up: start ## Start all services
	@if [ -z "${MAKE_BACKEND_COMMAND}" ]; \
		then sleep 2; \
		else \
		echo starting backend service: ${MAKE_BACKEND_COMMAND} \
		&& docker-compose exec backend /bin/bash -c "$(MAKE_BACKEND_COMMAND)"; \
	fi

datastore-update-index: start ## Update backend/index.yaml according to current indexes on datastore emulator
	@docker-compose exec backend cp -f /data/datastore/db/WEB-INF/index.yaml .

start:
	@docker-compose start

down: ## Stop all services
	@docker-compose stop || true

remove:  ## Delete containers
	@docker-compose down || true

logs: start ## Containers logs output
	@docker-compose logs -f

gcp-connect: start ## Connect to the GCP project
	@docker-compose exec gcp-deploy gcloud init

gcp-deploy: start ## Deploy source code to GCP
	@docker-compose exec gcp-deploy gcloud app deploy queue.yaml index.yaml app.yaml cron.yaml

gcp-browse: start ## Get the URL to your project on GCP
	@docker-compose exec gcp-deploy gcloud app browse

.DEFAULT_GOAL := help
