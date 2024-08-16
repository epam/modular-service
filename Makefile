
.DEFAULT_GOAL := test

DOCKER_EXECUTABLE := podman
CLI_VENV_NAME := cli_venv

SYNDICATE_EXECUTABLE_PATH ?= $(shell which syndicate)
SYNDICATE_CONFIG_PATH ?= .syndicate-config-main

SERVER_IMAGE_NAME := public.ecr.aws/x4s4z8e1/syndicate/modular-service
SERVER_IMAGE_TAG ?= $(shell python -c "from src.commons.__version__ import __version__; print(__version__)")


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

image-arm64:
	$(DOCKER_EXECUTABLE) build --platform linux/arm64 -t $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-arm64 .

image-amd64:
	$(DOCKER_EXECUTABLE) build --platform linux/amd64 -t $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-amd64 .


image-manifest:
	-$(DOCKER_EXECUTABLE) manifest rm $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)
	$(DOCKER_EXECUTABLE) manifest create $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG) $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-arm64 $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-amd64
	$(DOCKER_EXECUTABLE) manifest annotate $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG) $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-arm64 --arch arm64
	$(DOCKER_EXECUTABLE) manifest annotate $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG) $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-amd64 --arch amd64


push-arm64:
	$(DOCKER_EXECUTABLE) push $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-arm64


push-amd64:
	$(DOCKER_EXECUTABLE) push $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)-amd64

push-manifest:
	$(DOCKER_EXECUTABLE) manifest push $(SERVER_IMAGE_NAME):$(SERVER_IMAGE_TAG)


cli-dist:
	python -m build --sdist modular-service-cli/

