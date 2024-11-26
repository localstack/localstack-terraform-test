import logging
import os
from timeit import default_timer as timer

import click

from terraform_pytest.constants import (
    TF_REPO_PATH,
    TF_TEST_BINARY_PATH,
    TERRATEST_PROJECT_FOLDER,
)
from terraform_pytest.utils import (
    build_test_binary,
    get_services,
    patch_repository,
    run_terratest_tests,
)

logging.basicConfig(level=logging.INFO)


@click.group(name="pytest-golang", help="Golang Test Runner for localstack")
def cli():
    pass


@click.command(name="patch", help="Patch the golang test runner")
def patch_command():
    patch_repository()


@click.command(name="build", help="Build binary for testing")
@click.option(
    "--service",
    "-s",
    default=None,
    required=True,
    help="""Service to build; use "ls-all", "ls-community", "ls-pro" to build all services, example: 
--service=ls-all; --service=ec2; --service=ec2,iam""",
)
@click.option("--force-build", "-f", is_flag=True, default=False, help="Force rebuilds binary")
def build_command(service, force_build):
    services = get_services(service)

    for service in services:
        logging.info(f"Building {service}...")
        try:
            start_time = timer()
            build_test_binary(service=service, tf_root_path=TF_REPO_PATH, force_build=force_build)
            end_time = timer()
            logging.info(f"Build completed in {end_time - start_time:.2f} seconds")
        except KeyboardInterrupt:
            logging.error(
                "Operation was interrupted. The process may not have completed successfully."
            )
            logging.debug("Exception information:", exc_info=True)
            return  # Necessary to terminate all ongoing processes
        except Exception as e:
            logging.error(f"Failed to build binary for service '{service}': {str(e)}")


@click.command(name="clean", help="Cleans up all the binaries")
def clean_command():
    logging.info(f"Cleaning up {TF_TEST_BINARY_PATH}")

    if not os.path.exists(TF_TEST_BINARY_PATH):
        logging.info(f"{TF_TEST_BINARY_PATH}: does not exist")
        return
    for file in os.listdir(TF_TEST_BINARY_PATH):
        if file.endswith(".test"):
            logging.info(f"Removing: {file}")
            os.remove(os.path.join(TF_TEST_BINARY_PATH, file))
    logging.info("Done")


@click.command(name="terratest-tests", help="Run Golang Terratest tests")
def terratest_tests():
    logging.info(f"Running terratest tests from {TERRATEST_PROJECT_FOLDER} directory")

    try:
        _, output = run_terratest_tests(TERRATEST_PROJECT_FOLDER)
        print(output)
    except Exception as e:
        logging.error(f"Failed to execute terratest tests: {str(e)}")


if __name__ == "__main__":
    cli.add_command(build_command)
    cli.add_command(patch_command)
    cli.add_command(clean_command)
    cli.add_command(terratest_tests)
    cli()
