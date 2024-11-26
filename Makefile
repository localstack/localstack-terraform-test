SHELL := /bin/bash

VENV_BIN ?= python3 -m venv
VENV_DIR ?= .venv
PIP_CMD ?= pip3

ifeq ($(OS), Windows_NT)
	VENV_ACTIVATE = $(VENV_DIR)/Scripts/activate
else
	VENV_ACTIVATE = $(VENV_DIR)/bin/activate
endif

usage:						## Show this help in table format
	@echo "| Target                 | Description                                                       |"
	@echo "|------------------------|-------------------------------------------------------------------|"
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/:.*##\s*/##/g' | awk -F'##' '{ printf "| %-22s | %-65s |\n", $$1, $$2 }'

$(VENV_ACTIVATE):
	test -d $(VENV_DIR) || $(VENV_BIN) $(VENV_DIR)
	$(VENV_RUN); $(PIP_CMD) install --upgrade pip setuptools wheel plux
	touch $(VENV_ACTIVATE)

VENV_RUN = . $(VENV_ACTIVATE)

venv: $(VENV_ACTIVATE)		## Create a new (empty) virtual environment

install: venv				## Install the package in editable mode
	$(VENV_RUN); $(PIP_CMD) install -r requirements.txt
	@terraform -v >/dev/null 2>&1 || { echo >&2 "Terraform is not installed. Please install it by following the guide at https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli"; exit 1; }

init_precommit:				## Install the pre-commit hook into your local git repository
	($(VENV_RUN); pre-commit install)

lint:						## Run linting
	@echo "Running black... "
	$(VENV_RUN); black --check .

format:						## Run formatting
	$(VENV_RUN); python -m isort .; python -m black .

reset-submodules:			## Reset the submodules to the specified commit
	git submodule foreach git reset --hard

get-submodules:				## Get the submodules
	git submodule update --init --recursive

prepare-lambda:				## Prepare the lambda function for deployment
	@test -d terraform-provider-aws || echo "Please run 'git submodule update --init --recursive' to get the terraform-provider-aws submodule"
	@cp -r terraform-provider-aws/internal/service/lambda/test-fixtures ./test-bin/ && echo "Copied test-fixtures to test-bin"


.PHONY: usage venv install init_precommit lint format reset-submodules