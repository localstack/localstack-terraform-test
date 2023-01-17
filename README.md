# Localstack Terraform Test Runner

This is a test runner for localstack and terraform. It will run a test cases from the hashicrop [terraform provider aws](https://github.com/hashicorp/terraform-provider-aws.git) against Localstack Instance.

Purpose of this project is to externalize the test cases from the localstack repo and run them against localstack to gather parity metrics.

## Installation
1. Clone the repository with submodules`
2. Run `make venv` to create a virtual environment
3. Run `make install` to install the dependencies

## How to run?
1. Run `python -m terraform_pytest.main patch` to apply the patch to the terraform provider aws
2. Run `python -m terraform_pytest.main build -s s3` to build testing binary for the golang module
3Now you are ready to use `python -m pytest` commands to list and run test cases from golang

## How to run test cases?
- To list down all the test case from a specific service, run `python -m pytest terraform-provider-aws/internal/service/<service> --collect-only -q`
- To run a specific test case, run `python -m pytest terraform-provider-aws/internal/service/<service>/<test-file> -k <test-case-name> --ls-start` or `python -m pytest terraform-provider-aws/internal/service/<service>/<test-file>::<test-case-name> --ls-start`
- Additional environment variables can be added by appending it in the start of the command, i.e. `AWS_ALTERNATE_REGION='us-west-2' python -m pytest terraform-provider-aws/internal/service/<service>/<test-file>::<test-case-name> --ls-start`

## Default environment variables
- **TF_ACC**: `1`
- **AWS_ACCESS_KEY_ID**: `test`
- **AWS_SECRET_ACCESS_KEY**: `test`
- **AWS_DEFAULT_REGION**: `us-west-1`
- **AWS_ALTERNATE_ACCESS_KEY_ID**: `test`
- **AWS_ALTERNATE_SECRET_ACCESS_KEY**: `test`
- **AWS_ALTERNATE_SECRET_ACCESS_KEY**: `test`
- **AWS_ALTERNATE_REGION**: `us-east-2`
- **AWS_THIRD_REGION**: `eu-west-1`

## Options
- `--ls-start`: Start localstack instance before running the test cases
- `--ls-image`: Specify the localstack image to use, default is `localstack/localstack:latest`