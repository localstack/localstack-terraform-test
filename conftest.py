import os
import re
from os.path import dirname, realpath, relpath
from pathlib import Path

import docker
import pytest
import requests
from requests.adapters import HTTPAdapter, Retry

from terraform_pytest.utils import execute_command


def pytest_addoption(parser):
    """Add command line options to pytest"""
    parser.addoption(
        "--ls-image",
        action="store",
        default="localstack/localstack:latest",
        help="Base URL for the API tests",
    )
    parser.addoption(
        "--ls-start", action="store_true", default=False, help="Start localstack service"
    )


def pytest_collect_file(parent, file_path):
    """Collect test files from the test directory"""
    if file_path.suffix == ".go" and file_path.name.endswith("_test.go"):
        return GoFile.from_parent(parent, path=file_path)


class GoFile(pytest.File):
    def collect(self):
        """Collect test cases from the test file"""
        raw = self.path.open().read()
        fa = re.findall(r"^(func (TestAcc.*))\(.*\).*", raw, re.MULTILINE)
        for _, name in fa:
            yield GoItem.from_parent(self, name=name)


class GoItem(pytest.Item):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def runtest(self):
        """Run the test case"""

        tf_root_path = realpath(relpath(self.path).split(os.sep)[0])
        service_path = dirname(Path(*relpath(self.path).split(os.sep)[1:]))
        service = service_path.split(os.sep)[-1]

        env = dict(os.environ)
        env.update(
            {
                "TF_ACC": "1",
                "AWS_ACCESS_KEY_ID": "test",
                "AWS_SECRET_ACCESS_KEY": "test",
                "AWS_DEFAULT_REGION": "us-west-1",
                "AWS_ALTERNATE_ACCESS_KEY_ID": "test",
                "AWS_ALTERNATE_SECRET_ACCESS_KEY": "test",
                "AWS_ALTERNATE_SECRET_ACCESS_KEY": "test",
                "AWS_ALTERNATE_REGION": "us-east-2",
                "AWS_THIRD_REGION": "eu-west-1",
            }
        )

        cmd = [
            f"./test-bin/{service}.test",
            "-test.v",
            "-test.parallel=1",
            "-test.count=1",
            "-test.timeout=60m",
            f"-test.run={self.name}",
        ]
        return_code, stdout = execute_command(cmd, env, tf_root_path)
        if return_code != 0:
            raise GoException(returncode=return_code, stderr=stdout)

    def repr_failure(self, excinfo, **kwargs):
        """Called when self.runtest() raises an exception.

        return: a representation of a collection failure.
        """
        if isinstance(excinfo.value, GoException):
            return "\n".join(
                [
                    f"Execution failed with return code: {excinfo.value.returncode}",
                    f"Failure Reason:\n{excinfo.value.stderr}",
                ]
            )

    def reportinfo(self):
        """Get location information for this item for test reports.

        return: a tuple with three elements:
        - The path of the test
        - The line number of the test
        - A name of the test to be shown in reports
        """
        return self.path, 0, f"Test Case: {self.name}"


class GoException(Exception):
    """Go test exception - raised when test cases failed"""

    def __init__(self, returncode, stderr):
        self.returncode = returncode
        self.stderr = stderr


def _docker_service_health(client):
    """Check if the docker service is healthy"""
    if not client.ping():
        print("\nPlease start docker daemon and try again")
        raise Exception("Docker is not running")


def _start_docker_container(client, config, localstack_image):
    """Start the docker container"""
    env_vars = ["DEBUG=1", "PROVIDER_OVERRIDE_S3=asf", "FAIL_FAST=1"]
    port_mappings = {
        "53/tcp": ("127.0.0.1", 53),
        "53/udp": ("127.0.0.1", 53),
        "443": ("127.0.0.1", 443),
        "4566": ("127.0.0.1", 4566),
        "4571": ("127.0.0.1", 4571),
    }
    volumes = ["/var/run/docker.sock:/var/run/docker.sock"]
    localstack_container = client.containers.run(
        image=localstack_image,
        detach=True,
        ports=port_mappings,
        name="localstack_main",
        volumes=volumes,
        auto_remove=True,
        environment=env_vars,
    )
    setattr(config, "localstack_container_id", localstack_container.id)


def _stop_docker_container(client, config):
    """Stop the docker container"""
    client.containers.get(getattr(config, "localstack_container_id")).stop()
    print("LocalStack is stopped")


def _localstack_health_check():
    """Check if the localstack service is healthy"""
    localstack_health_url = "http://localhost:4566/health"
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=2)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.get(localstack_health_url)
    session.close()


def _pull_docker_image(client, localstack_image):
    """Pull the docker image"""
    docker_image_list = client.images.list(name=localstack_image)
    if len(docker_image_list) == 0:
        print(f"Pulling image {localstack_image}")
        client.images.pull(localstack_image)
    docker_image_list = client.images.list(name=localstack_image)
    print(f"Using LocalStack image: {docker_image_list[0].id}")


def pytest_sessionstart(session):
    """Called after the Session object has been created and before performing collection and entering the run test loop."""
    is_collect_only = session.config.getoption(name="--collect-only")
    is_localstack_start = session.config.getoption(name="--ls-start")
    localstack_image = session.config.getoption(name="--ls-image")

    if getattr(session.config, "workerinput", None) is not None:
        return

    if not is_collect_only and is_localstack_start:
        print("\nStarting LocalStack...")

        client = docker.from_env()
        _docker_service_health(client)
        _pull_docker_image(client, localstack_image)
        _start_docker_container(client, session.config, localstack_image)
        _localstack_health_check()
        client.close()

        print("LocalStack is ready...")


def pytest_sessionfinish(session, exitstatus):
    """Called after whole test run finished, right before returning the exit status to the system."""
    is_collect_only = session.config.getoption(name="--collect-only")
    is_localstack_start = session.config.getoption(name="--ls-start")

    # Only run on the master node
    if getattr(session.config, "workerinput", None) is not None:
        return

    if not is_collect_only and is_localstack_start:
        print("\nStopping LocalStack...")
        client = docker.from_env()
        _stop_docker_container(client, session.config)
        client.close()
