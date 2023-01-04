import pytest
import re
from subprocess import PIPE, Popen
from pathlib import Path
import os
from os.path import realpath, relpath, dirname
import docker
import requests
from requests.adapters import HTTPAdapter, Retry
from os.path import exists


def pytest_addoption(parser):
    parser.addoption(
        '--ls-image', action='store', default='localstack/localstack:latest', help='Base URL for the API tests'
    )
    parser.addoption(
        '--ls-start', action='store_true', default=False, help='Start localstack service'
    )


def pytest_collect_file(parent, file_path):
    if file_path.suffix == ".go" and file_path.name.endswith("_test.go"):
        return GoFile.from_parent(parent, path=file_path)


class GoFile(pytest.File):
    def collect(self):
        raw = self.path.open().read()
        fa = re.findall(r"^(func (TestAcc.*))\(.*\).*", raw, re.MULTILINE)
        for _, name in fa:
            yield GoItem.from_parent(self, name=name)


class GoItem(pytest.Item):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def runtest(self):
        tf_root_path = realpath(relpath(self.path).split(os.sep)[0])
        service_path = dirname(Path(*relpath(self.path).split(os.sep)[1:]))
        service = service_path.split(os.sep)[-1]

        _build_test_bin(service=service, tf_root_path=tf_root_path, service_path=service_path)

        env = dict(os.environ)
        env.update({
            'TF_ACC': '1',
            'AWS_ACCESS_KEY_ID': 'test',
            'AWS_SECRET_ACCESS_KEY': 'test',
            'AWS_DEFAULT_REGION': 'us-east-1'
        })

        cmd = [
            f"./test-bin/{service}.test",
            "-test.v",
            "-test.parallel=1",
            "-test.count=1",
            "-test.timeout=60m",
            "-test.run", f"{self.name}"
        ]

        proc = Popen(
            cmd, stdout=PIPE, stderr=PIPE,
            env=env, bufsize=1, universal_newlines=True,
            cwd=tf_root_path
        )
        stdout, stderr = proc.communicate()
        proc.terminate()
        if proc.returncode != 0:
            raise GoException(proc.returncode, stdout, stderr)
        return proc.returncode

    def repr_failure(self, excinfo, **kwargs):
        """Called when self.runtest() raises an exception."""
        if isinstance(excinfo.value, GoException):
            return "\n".join(
                [
                    f'\nExecution failed with return code: {excinfo.value.returncode}',
                    f'\nFailure Reason:\n{excinfo.value}',
                ]
            )

    def reportinfo(self):
        return self.path, 0, f"Test Case: {self.name}"


class GoException(Exception):
    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _build_test_bin(service, tf_root_path, service_path):
    bin_path = f'./test-bin/{service}.test'

    if exists(f"{tf_root_path}/{bin_path}"):
        return
    cmd = [
        "go",
        "test",
        "-c",
        f"./{service_path}",
        "-o",
        bin_path,
    ]
    proc = Popen(
        cmd, stdout=PIPE, stderr=PIPE,
        bufsize=1, universal_newlines=True,
        cwd=tf_root_path
    )
    stdout, stderr = proc.communicate()
    proc.terminate()
    if proc.returncode != 0:
        raise GoException(proc.returncode, stdout, stderr)
    return


def _docker_service_health(client):
    if not client.ping():
        print("\nPlease start docker daemon and try again")
        raise Exception("Docker is not running")


def _start_docker_container(client, config, localstack_image):
    env_vars = ["DEBUG=1"]
    port_mappings = {
        '53/tcp': ('127.0.0.1', 53),
        '53/udp': ('127.0.0.1', 53),
        '443': ('127.0.0.1', 443),
        '4566': ('127.0.0.1', 4566),
        '4571': ('127.0.0.1', 4571),
    }
    volumes = ["/var/run/docker.sock:/var/run/docker.sock"]
    localstack_container = client.containers.run(image=localstack_image, detach=True, ports=port_mappings,
                                                 name='localstack_main', volumes=volumes, auto_remove=True,
                                                 environment=env_vars)
    setattr(config, "localstack_container_id", localstack_container.id)


def _stop_docker_container(client, config):
    client.containers.get(getattr(config, "localstack_container_id")).stop()
    print("LocalStack is stopped")


def _localstack_health_check():
    localstack_health_url = "http://localhost:4566/health"
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=2)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.get(localstack_health_url)


def _pull_docker_image(client, localstack_image):
    docker_image_list = client.images.list(name=localstack_image)
    if len(docker_image_list) == 0:
        print(f"Pulling image {localstack_image}")
        client.images.pull(localstack_image)
    docker_image_list = client.images.list(name=localstack_image)
    print(f"Using LocalStack image: {docker_image_list[0].id}")


def pytest_configure(config):
    is_collect_only = config.getoption(name='--collect-only')
    is_localstack_start = config.getoption(name='--ls-start')
    localstack_image = config.getoption(name='--ls-image')

    if not is_collect_only and is_localstack_start:

        print("\nStarting LocalStack...")

        client = docker.from_env()
        _docker_service_health(client)
        _pull_docker_image(client, localstack_image)
        _start_docker_container(client, config, localstack_image)
        _localstack_health_check()
        client.close()

        print("LocalStack is ready...")


def pytest_unconfigure(config):
    is_collect_only = config.getoption(name='--collect-only')
    is_localstack_start = config.getoption(name='--ls-start')

    if not is_collect_only and is_localstack_start:
        print("\nStopping LocalStack...")
        client = docker.from_env()
        _stop_docker_container(client, config)
        client.close()