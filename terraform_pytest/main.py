from os.path import realpath
from timeit import default_timer as timer

import click

from terraform_pytest.utils import TF_REPO_NAME, build_test_bin, get_services, patch_repo


@click.group(name="pytest-golang", help="Golang Test Runner for localstack")
def cli():
    pass


@click.command(name="patch", help="Patch the golang test runner")
def patch():
    patch_repo()


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
def build(service, force_build):
    services = get_services(service)

    for service in services:
        print(f"Building {service}...")
        try:
            start = timer()
            build_test_bin(
                service=service, tf_root_path=realpath(TF_REPO_NAME), force_build=force_build
            )
            end = timer()
            print(f"Build {service} in {end - start} seconds")
        except KeyboardInterrupt:
            print("Interrupted")
            return
        except Exception as e:
            print(f"Failed to build binary for {service}: {e}")


if __name__ == "__main__":
    cli.add_command(build)
    cli.add_command(patch)
    cli()
