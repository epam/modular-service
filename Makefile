
.DEFAULT_GOAL := test

DOCKER_EXECUTABLE := podman
CLI_VENV_NAME := cli_venv

SYNDICATE_EXECUTABLE_PATH ?= $(shell which syndicate)
SYNDICATE_CONFIG_PATH ?= .syndicate-config-main

SERVER_IMAGE_NAME := modular-service
SERVER_IMAGE_TAG := latest


check-syndicate:
	@if [[ -z "$(SYNDICATE_EXECUTABLE_PATH)" ]]; then echo "No syndicate executable found"; exit 1; fi
	@if [[ ! -d "$(SYNDICATE_CONFIG_PATH)" ]]; then echo "Syndicate config directory $(SYNDICATE_CONFIG_PATH) not found"; exit 1; fi


test:
	pytest tests/


install:
	@if [[ -z "$(VIRTUAL_ENV)" ]]; then echo "Creating python virtual env"; python -m venv venv; fi
	venv/bin/pip install -r src/requirements.txt
	@echo "Execute:\nsource ./venv/bin/activate"


install-cli:
	# installing CLI in editable mode
	python -m venv $(CLI_VENV_NAME)
	$(CLI_VENV_NAME)/bin/pip install -e ./modular-service-cli
	@echo "Execute:\nsource ./$(CLI_VENV_NAME)/bin/activate"


clean:
	-rm -rf .pytest_cache .coverage ./logs htmlcov
	-if [[ -d "$(SYNDICATE_CONFIG_PATH)/logs" ]]; then rm -rf "$(SYNDICATE_CONFIG_PATH)/logs"; fi
	-if [[ -d "$(SYNDICATE_CONFIG_PATH)/bundles" ]]; then rm -rf "$(SYNDICATE_CONFIG_PATH)/bundles"; fi

image:
	$(DOCKER_EXECUTABLE) build -t $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG) .


cli-dist:
	python -m build --sdist modular-service-cli/

