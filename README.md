# Localstack Terraform Test Runner

This is a test runner for localstack and terraform. It will run a test cases from the hashicrop [terraform provider aws](https://github.com/hashicorp/terraform-provider-aws.git) against Localstack Instance.

Purpose of this project is to externalize the test cases from the localstack repo and run them against localstack to gather parity metrics.

## Installation
1. Clone the repository
2. Run `python -m virtualenv venv` to create a virtual environment
3. Run `source venv/bin/activate` to activate the virtual environment
4. Run `pip install -r requirements.txt` to install the dependencies

## How to run?
1. Run `python main.py patch` to apply the patch to the terraform provider aws
2. Now you are ready to use `pytest` commands to list and run test cases from golang

## How to run test cases?
- To list down all the test case from a specific service, run `pytest terraform-provider-aws/internal/service/<service> --collect-only -q`
- To run a specific test case, run `pytest terraform-provider-aws/internal/service/<service>/<test-file> -k <test-case-name> --ls-start` or `pytest terraform-provider-aws/internal/service/<service>/<test-file>::<test-case-name> --ls-start`
- Additional environment variables can be added by appending it in the start of the command, i.e. `AWS_ALTERNATE_REGION='us-west-2' pytest terraform-provider-aws/internal/service/<service>/<test-file>::<test-case-name> --ls-start`

## Default environment variables
- **TF_LOG**: ``debug``,
- **TF_ACC**: ``1``,
- **AWS_ACCESS_KEY_ID**: ``test``,
- **AWS_SECRET_ACCESS_KEY**: ``test``,
- **AWS_DEFAULT_REGION**: ``'us-east-1``'

## Options
- `--ls-start`: Start localstack instance before running the test cases
- `--ls-image`: Specify the localstack image to use, default is `localstack/localstack:latest`