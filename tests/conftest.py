import re
import pytest
import docker
import requests
from requests.adapters import HTTPAdapter, Retry
from pathlib import Path
import os
from os.path import realpath, relpath, dirname
from utils import execute_command, build_test_bin


def pytest_addoption(parser):
    parser.addoption(
        '--ls-image', action='store', default='localstack/localstack:latest', help='Base URL for the API tests'
    )
    parser.addoption(
        '--ls-start', action='store_true', default=False, help='Start localstack service'
    )


def pytest_collect_file(parent, file_path):
    if file_path.suffix == '.go' and file_path.name.endswith('_test.go'):
        return GoFile.from_parent(parent, path=file_path)


class GoFile(pytest.File):
    def collect(self):
        raw = self.path.open().read()
        fa = re.findall(r'^(func (TestAcc.*))\(.*\).*', raw, re.MULTILINE)
        for _, name in fa:
            yield GoItem.from_parent(self, name=name)


class GoItem(pytest.Item):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def runtest(self):
        tf_root_path = realpath(relpath(self.path).split(os.sep)[0])
        service_path = dirname(Path(*relpath(self.path).split(os.sep)[1:]))
        service = service_path.split(os.sep)[-1]

        env = dict(os.environ)
        env.update({
            'TF_ACC': '1',
            'AWS_ACCESS_KEY_ID': 'test',
            'AWS_SECRET_ACCESS_KEY': 'test',
            'AWS_DEFAULT_REGION': 'us-west-1',
            'AWS_ALTERNATE_ACCESS_KEY_ID': 'test',
            'AWS_ALTERNATE_SECRET_ACCESS_KEY': 'test',
            'AWS_ALTERNATE_SECRET_ACCESS_KEY': 'test',
            'AWS_ALTERNATE_REGION': 'us-east-2',
            'AWS_THIRD_REGION': 'eu-west-1',
        })

        cmd = [
            f'./test-bin/{service}.test',
            '-test.v',
            '-test.parallel=1',
            '-test.count=1',
            '-test.timeout=60m',
            f'-test.run={self.name}',
        ]
        return_code, stdout = execute_command(cmd, env, tf_root_path)
        if return_code != 0:
            raise GoException(returncode=return_code, stderr=stdout)

    def repr_failure(self, excinfo, **kwargs):
        if isinstance(excinfo.value, GoException):
            return '\n'.join(
                [
                    f'Execution failed with return code: {excinfo.value.returncode}',
                    f'Failure Reason:\n{excinfo.value.stderr}',
                ]
            )

    def reportinfo(self):
        return self.path, 0, f'Test Case: {self.name}'


class ReprCrash:
    def __init__(self, message):
        self.message = message


class LongRepr:
    def __init__(self, message, reason):
        self.reprcrash = ReprCrash(message)
        self.reason = reason

    def __str__(self):
        return self.reason


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.failed:
        splits = report.longrepr.split('\n', 1)
        longrepr = LongRepr(splits[0], splits[1])
        delattr(report, 'longrepr')
        setattr(report, 'longrepr', longrepr)


class GoException(Exception):
    def __init__(self, returncode, stderr):
        self.returncode = returncode
        self.stderr = stderr


def _docker_service_health(client):
    if not client.ping():
        print('\nPlease start docker daemon and try again')
        raise Exception('Docker is not running')


def _start_docker_container(client, config, localstack_image):
    env_vars = ['DEBUG=1', 'PROVIDER_OVERRIDE_S3=asf']
    port_mappings = {
        '53/tcp': ('127.0.0.1', 53),
        '53/udp': ('127.0.0.1', 53),
        '443': ('127.0.0.1', 443),
        '4566': ('127.0.0.1', 4566),
        '4571': ('127.0.0.1', 4571),
    }
    volumes = ['/var/run/docker.sock:/var/run/docker.sock']
    localstack_container = client.containers.run(image=localstack_image, detach=True, ports=port_mappings,
                                                 name='localstack_main', volumes=volumes, auto_remove=True,
                                                 environment=env_vars)
    setattr(config, 'localstack_container_id', localstack_container.id)


def _stop_docker_container(client, config):
    client.containers.get(getattr(config, 'localstack_container_id')).stop()
    print('LocalStack is stopped')


def _localstack_health_check():
    localstack_health_url = 'http://localhost:4566/health'
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=2)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    session.get(localstack_health_url)
    session.close()


def _pull_docker_image(client, localstack_image):
    docker_image_list = client.images.list(name=localstack_image)
    if len(docker_image_list) == 0:
        print(f'Pulling image {localstack_image}')
        client.images.pull(localstack_image)
    docker_image_list = client.images.list(name=localstack_image)
    print(f'Using LocalStack image: {docker_image_list[0].id}')


def pytest_configure(config):
    is_collect_only = config.getoption(name='--collect-only')
    is_localstack_start = config.getoption(name='--ls-start')
    localstack_image = config.getoption(name='--ls-image')

    if not is_collect_only and is_localstack_start:
        print('\nStarting LocalStack...')

        client = docker.from_env()
        _docker_service_health(client)
        _pull_docker_image(client, localstack_image)
        _start_docker_container(client, config, localstack_image)
        _localstack_health_check()
        client.close()

        print('LocalStack is ready...')


def pytest_unconfigure(config):
    is_collect_only = config.getoption(name='--collect-only')
    is_localstack_start = config.getoption(name='--ls-start')

    if not is_collect_only and is_localstack_start:
        print('\nStopping LocalStack...')
        client = docker.from_env()
        _stop_docker_container(client, config)
        client.close()
