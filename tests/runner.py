import logging
import os
import time
from queue import Queue
from subprocess import Popen, PIPE
from threading import Thread, Timer
from typing import Tuple, List, Dict

import pytest

logger = logging.getLogger(__name__)

root_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))

test_bin = os.path.join(os.path.expanduser('~'), '.cache/localstack/aws.test')
test_log_dir = os.path.join(root_dir, 'target/logs')

timeout_seconds = 5 * 60  # 5 minute timeout per test

TestResult = Tuple[int, List[str]]


def reader(pipe, queue: Queue):
    try:
        with pipe:
            for line in iter(pipe.readline, ''):
                queue.put((pipe, line))
    except ValueError as e:
        if 'closed file' in str(e):
            pass
    finally:
        queue.put(None)


def get_run_test_cmd(service_name: str, test: str) -> Tuple[List[str], Dict]:
    if os.environ.get("USE_TEST_BIN", "").strip() in ["1", "true"]:
        return [test_bin, '-test.v', '-test.parallel=1', '-test.run', f'{test}$'], {}
    kwargs = {"cwd": "./terraform-provider-aws"}
    return ["go", "test", f"./internal/service/{service_name}", '-test.parallel=1', '-test.v', '-test.run', test], kwargs


def run_test(test: str) -> TestResult:
    if not os.path.exists(test_log_dir):
        os.makedirs(test_log_dir, exist_ok=True)

    then = time.time()

    env = dict(os.environ)
    env.update({
        'TF_LOG': 'debug',
        'TF_ACC': '1',
        'AWS_ACCESS_KEY_ID': 'test',
        'AWS_SECRET_ACCESS_KEY': 'test',
        'AWS_DEFAULT_REGION': 'us-east-1'
    })

    service_name, test = test.split(":", maxsplit=1)
    logger.warning("run_test %s", test)
    cmd, run_kwargs = get_run_test_cmd(service_name, test)

    proc = Popen(cmd, env=env, stdout=PIPE, stderr=PIPE, bufsize=1, universal_newlines=True, **run_kwargs)
    lines = Queue()
    stdout = []

    stderr_log = os.path.join(test_log_dir, f'{test}.stderr.log')
    stdout_log = os.path.join(test_log_dir, f'{test}.stdout.log')

    stdout_log_fd = open(stdout_log, 'w')
    stderr_log_fd = open(stderr_log, 'w')

    t_stdout = Thread(target=reader, args=[proc.stdout, lines])
    t_stderr = Thread(target=reader, args=[proc.stderr, lines])

    t_stdout.start()
    t_stderr.start()

    def timeout():
        proc.terminate()

        duration = time.time() - then
        lines = [
            f'TEST TERMINATED (timeout {timeout_seconds}s)\n',
            f'--- ERROR: {test} ({duration:.2f}s)\n',
            'ERROR\n'
        ]

        stdout.extend(lines)
        stdout_log_fd.writelines(lines)
        stderr_log_fd.writelines(lines)

    timer = Timer(timeout_seconds, timeout)
    timer.start()

    try:
        for source, line in iter(lines.get, None):
            if source == proc.stdout:
                stdout.append(line)
                stdout_log_fd.write(line)
                continue

            # source == proc.stderr
            stderr_log_fd.write(line)

            if 'attempt 2/' in line:
                duration = time.time() - then
                lines = [
                    'TEST TERMINATED (likely 4xx/5xx errors)\n',
                    f'--- ERROR: {test} ({duration:.2f}s)\n',
                    'ERROR\n'
                ]

                stdout.extend(lines)
                stdout_log_fd.writelines(lines)
                stderr_log_fd.writelines(lines)
                break
    finally:
        timer.cancel()

        proc.stderr.close()
        proc.stdout.close()

        proc.wait()

        t_stderr.join(5)
        t_stdout.join(5)

        stdout_log_fd.flush()
        stderr_log_fd.flush()

        stdout_log_fd.close()
        stderr_log_fd.close()

    return proc.returncode, stdout


def create_fail_message(stdout):
    if not os.environ.get("PRINT_LOGS"):
        return ''
    result = list()
    for line in stdout[:-1]:
        if line.startswith('=== ') or line.startswith('--- '):
            continue
        result.append(line)
    return ''.join(result)


def assert_test(test):
    rc, stdout = run_test(test)

    if stdout and stdout[-1] == 'SKIP':
        pytest.skip('skipped: ' + create_fail_message(stdout))
        return

    if rc == 0:
        return
    if rc == -13:
        pytest.fail(create_fail_message(stdout), False)
        return

    pytest.fail(create_fail_message(stdout), False)
    return
